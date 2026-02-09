"""Note management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.schemas.note import NoteListResponse, NoteResponse, NoteUploadResponse
from app.services.note_service import NoteService
from app.services.ocr_service import ocr_service
from app.services.oss_service import oss_service
from app.services.virus_scan_service import virus_scan_service

# Rate limiter: 10 requests per minute per IP for uploads
upload_limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/api/notes", tags=["Notes"])


async def read_file_in_chunks(
    file: UploadFile,
    chunk_size: int = 8192,
    max_size: int = 10485760
) -> bytes:
    """Read file in chunks to prevent memory exhaustion.

    Args:
        file: UploadFile to read
        chunk_size: Size of each chunk in bytes
        max_size: Maximum file size in bytes

    Returns:
        File content as bytes

    Raises:
        HTTPException: If file size exceeds max_size
    """
    content = b""
    total_size = 0

    while chunk := await file.read(chunk_size):
        total_size += len(chunk)

        if total_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {max_size} bytes"
            )

        content += chunk
        logger.debug(
            f"Read {total_size} bytes of {file.filename}",
            extra={
                "filename": file.filename,
                "bytes_read": total_size,
                "action": "file_upload_progress"
            }
        )

    return content

@router.post("/upload", response_model=NoteUploadResponse)
@upload_limiter.limit("10/minute")
async def upload_note(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    category_id: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a note file with OCR recognition."""
    from app.core.config import settings
    
    user, _ = current_user

    logger.info(
        "File upload started",
        extra={
            "user_id": str(user.id),
            "filename": file.filename,
            "action": "file_upload_start"
        }
    )

    try:
        # Validate Content-Length header first
        content_length = file.size if hasattr(file, 'size') else None
        if content_length and content_length > settings.MAX_UPLOAD_SIZE:
            logger.warning(
                "File too large from Content-Length",
                extra={
                    "user_id": str(user.id),
                    "content_length": content_length,
                    "max_size": settings.MAX_UPLOAD_SIZE,
                    "action": "file_upload_size_exceeded"
                }
            )
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
            )

        # Read file in chunks to prevent memory exhaustion
        file_content = await read_file_in_chunks(
            file,
            chunk_size=8192,
            max_size=settings.MAX_UPLOAD_SIZE
        )
        file_size = len(file_content)
        content_type = file.content_type

        logger.info(
            "File read successfully",
            extra={
                "user_id": str(user.id),
                "filename": file.filename,
                "file_size": file_size,
                "action": "file_read_complete"
            }
        )
        
        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
            )
        
        # Validate file type using extension
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required",
            )
        
        file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )
        
        # Validate MIME type using magic numbers
        try:
            import magic
            mime = magic.from_buffer(file_content, mime=True)
            
            # Define allowed MIME types
            allowed_mimes = {
                'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
                'application/pdf'
            }
            
            if mime not in allowed_mimes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file content type '{mime}'. File may be corrupted or renamed.",
                )
        except ImportError:
            # Fallback: python-magic not available, skip validation
            pass
        except Exception as e:
            # If magic detection fails, log but continue
            from loguru import logger
            logger.warning(f"MIME type detection failed: {e}")
        
        # Virus scanning
        scan_result = await virus_scan_service.scan_file(file_content, file.filename)
        if scan_result["found_infected"]:
            raise HTTPException(
                status_code=400,
                detail=f"File infected with viruses: {', '.join(scan_result['viruses'])}",
            )
        
        # Upload to OSS
        file_url = await oss_service.upload_file(
            file_content=file_content,
            filename=file.filename,
            content_type=content_type,
        )
        
        # OCR recognition with retry logic
        ocr_text = None
        ocr_confidence = None
        if content_type and content_type.startswith("image/"):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(
                        f"OCR recognition attempt {attempt + 1}",
                        extra={
                            "user_id": str(user.id),
                            "filename": file.filename,
                            "attempt": attempt + 1,
                            "action": "ocr_attempt"
                        }
                    )
                    ocr_text, ocr_confidence = await ocr_service.recognize_text_accurate(file_content)
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(
                            f"OCR recognition failed after {max_retries} attempts",
                            extra={
                                "user_id": str(user.id),
                                "filename": file.filename,
                                "error": str(e),
                                "action": "ocr_failed"
                            }
                        )
                        # Continue without OCR rather than failing entirely
                        ocr_text = None
                        ocr_confidence = None
                    else:
                        logger.warning(
                            f"OCR recognition attempt {attempt + 1} failed, retrying",
                            extra={
                                "user_id": str(user.id),
                                "filename": file.filename,
                                "error": str(e),
                                "action": "ocr_retry"
                            }
                        )
                        import asyncio
                        await asyncio.sleep(1)  # Wait before retry
        
        # Determine file type
        if content_type and content_type.startswith("image/"):
            file_type = "image"
        elif content_type and "pdf" in content_type.lower():
            file_type = "pdf"
        else:
            file_type = "text"
        
        # Create note
        from app.schemas.note import NoteCreate
        
        note_data = NoteCreate(
            title=title,
            file_url=file_url,
            thumbnail_url=None,
            ocr_text=ocr_text,
            category_id=uuid.UUID(category_id) if category_id else None,
            tags=[tag.strip() for tag in tags.split(",")] if tags else [],
            meta_data={"original_filename": file.filename, "file_size": file_size},
        )
        
        note_service = NoteService(db)
        note = await note_service.create_note(user.id, note_data)
        
        return NoteUploadResponse(
            note=NoteResponse.model_validate(note),
            ocr_confidence=ocr_confidence,
            file_size=file_size,
            content_type=content_type or "application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to upload note",
            extra={
                "user_id": str(user.id),
                "filename": file.filename if file.filename else "unknown",
                "error": str(e),
                "error_type": type(e).__name__,
                "action": "note_upload_error"
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process file upload. Please try again or contact support if the problem persists.",
        )

@router.get("")
async def get_notes(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[str] = None,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notes for current user."""
    user, _ = current_user
    tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    note_service = NoteService(db)
    notes, total = await note_service.get_notes(
        user_id=user.id,
        skip=skip,
        limit=limit,
        category_id=uuid.UUID(category_id) if category_id else None,
        search=search,
        tags=tag_list,
    )
    
    return NoteListResponse(
        notes=[NoteResponse.model_validate(note) for note in notes],
        total=total,
        page=skip // limit + 1,
        limit=limit,
    )

@router.get("/{note_id}")
async def get_note(
    note_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific note."""
    user, _ = current_user
    note_service = NoteService(db)
    note = await note_service.get_note(uuid.UUID(note_id), user.id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return NoteResponse.model_validate(note)

@router.delete("/{note_id}", status_code=204)
async def delete_note(
    note_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a note."""
    user, _ = current_user
    note_service = NoteService(db)
    success = await note_service.delete_note(uuid.UUID(note_id), user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")

@router.post("/{note_id}/favorite")
async def toggle_favorite(
    note_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle note favorite status."""
    user, _ = current_user
    note_service = NoteService(db)
    note = await note_service.toggle_favorite(uuid.UUID(note_id), user.id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return NoteResponse.model_validate(note)


@router.post("/ocr")
async def recognize_text(
    file: UploadFile = File(...),
    current_user: tuple = Depends(get_current_active_user),
):
    """Recognize text from image using OCR."""
    from app.schemas.note import OCRResponse
    
    user, _ = current_user
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are supported for OCR",
        )
    
    try:
        file_content = await file.read()
        
        # OCR recognition
        text, confidence = await ocr_service.recognize_text_accurate(file_content)
        
        if text is None:
            raise HTTPException(
                status_code=500,
                detail="OCR recognition failed",
            )
        
        return OCRResponse(
            text=text,
            confidence=confidence,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "OCR recognition failed",
            extra={
                "user_id": str(user.id),
                "error": str(e),
                "error_type": type(e).__name__,
                "action": "ocr_recognition_error"
            }
        )
        raise HTTPException(
            status_code=500,
            detail="Text recognition failed. Please ensure the image is clear and try again.",
        )
