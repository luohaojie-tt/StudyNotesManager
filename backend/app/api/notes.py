"""Note management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.schemas.note import NoteListResponse, NoteResponse, NoteUploadResponse
from app.services.note_service import NoteService
from app.services.ocr_service import ocr_service
from app.services.oss_service import oss_service

router = APIRouter(prefix="/api/notes", tags=["Notes"])

@router.post("/upload", response_model=NoteUploadResponse)
async def upload_note(
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
    try:
        file_content = await file.read()
        file_size = len(file_content)
        content_type = file.content_type
        
        # Validate file size
        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes",
            )
        
        # Validate file type
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
        
        # Upload to OSS
        file_url = await oss_service.upload_file(
            file_content=file_content,
            filename=file.filename,
            content_type=content_type,
        )
        
        # OCR recognition
        ocr_text = None
        ocr_confidence = None
        if content_type and content_type.startswith("image/"):
            ocr_text, ocr_confidence = await ocr_service.recognize_text_accurate(file_content)
        
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
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload note: {str(e)}",
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
        raise HTTPException(
            status_code=500,
            detail=f"OCR recognition failed: {str(e)}",
        )
