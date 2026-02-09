"""Mindmap management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.services.mindmap_service import MindmapService
from app.services.deepseek_service import DeepSeekService
from app.services.cache_service import cache_service

router = APIRouter(prefix="/api/mindmaps", tags=["Mindmaps"])


class MindmapGenerateRequest(BaseModel):
    """Request model for mindmap generation."""

    max_levels: int = Field(default=5, ge=1, le=10, description="Maximum hierarchy levels (1-10)")

    @field_validator("max_levels")
    @classmethod
    def validate_max_levels(cls, v: int) -> int:
        """Validate max_levels is within safe range."""
        if not 1 <= v <= 10:
            raise ValueError("max_levels must be between 1 and 10")
        return v


@router.post("/generate/{note_id}")
async def generate_mindmap(
    note_id: str,
    max_levels: int = 5,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a mindmap from a note using AI.

    Args:
        note_id: Note ID
        max_levels: Maximum hierarchy levels (1-10)
    """
    user, _ = current_user
    
    logger.info(
        "Mindmap generation requested",
        extra={
            "user_id": str(user.id),
            "note_id": note_id,
            "max_levels": max_levels,
            "action": "mindmap_generate_start"
        }
    )
    
    # Validate max_levels parameter
    if not 1 <= max_levels <= 10:
        logger.warning(
            "Invalid max_levels parameter",
            extra={
                "user_id": str(user.id),
                "note_id": note_id,
                "max_levels": max_levels,
                "action": "mindmap_generate_validation_failed"
            }
        )
        raise HTTPException(
            status_code=400,
            detail="max_levels must be between 1 and 10"
        )
    
    try:
        # Get note content
        from app.models.note import Note
        from sqlalchemy import select

        result = await db.execute(
            select(Note).where(Note.id == uuid.UUID(note_id)).where(Note.user_id == user.id)
        )
        note = result.scalar_one_or_none()

        if not note:
            logger.warning(
                "Note not found for mindmap generation",
                extra={
                    "user_id": str(user.id),
                    "note_id": note_id,
                    "action": "mindmap_generate_note_not_found"
                }
            )
            raise HTTPException(status_code=404, detail="Note not found")

        logger.debug(
            "Note found, starting AI generation",
            extra={
                "user_id": str(user.id),
                "note_id": note_id,
                "note_title": note.title,
                "content_length": len(note.content or note.ocr_text or ""),
                "action": "mindmap_generate_ai_start"
            }
        )

        note_content = note.content or note.ocr_text or ""
        
        # Check cache first
        cached_structure = await cache_service.get_cached_mindmap(
            note_content=note_content,
            max_levels=max_levels
        )
        
        if cached_structure:
            # Use cached structure - still save to DB for user
            logger.info(
                "Using cached mindmap structure",
                extra={
                    "user_id": str(user.id),
                    "note_id": note_id,
                    "action": "mindmap_using_cache"
                }
            )
            
            mindmap_service = MindmapService(db)
            mindmap = await mindmap_service.generate_mindmap(
                note_id=uuid.UUID(note_id),
                user_id=user.id,
                note_content=note_content,
                note_title=note.title,
                _cached_structure=cached_structure,
            )
            await mindmap_service.close()
        else:
            # Generate new mindmap
            mindmap_service = MindmapService(db)
            mindmap = await mindmap_service.generate_mindmap(
                note_id=uuid.UUID(note_id),
                user_id=user.id,
                note_content=note_content,
                note_title=note.title,
            )
            await mindmap_service.close()
            
            # Cache the generated structure
            await cache_service.cache_mindmap(
                note_content=note_content,
                max_levels=max_levels,
                mindmap_structure=mindmap.structure,
            )

        logger.info(
            "Mindmap generated successfully",
            extra={
                "user_id": str(user.id),
                "note_id": note_id,
                "mindmap_id": str(mindmap.id),
                "ai_model": mindmap.ai_model,
                "version": mindmap.version,
                "action": "mindmap_generate_success"
            }
        )

        return {
            "id": str(mindmap.id),
            "noteId": str(mindmap.note_id),
            "structure": mindmap.structure,
            "aiModel": mindmap.ai_model,
            "version": mindmap.version,
            "createdAt": mindmap.created_at.isoformat(),
        }
    except ValueError as e:
        logger.error(
            "Validation error during mindmap generation",
            extra={
                "user_id": str(user.id),
                "note_id": note_id,
                "error": str(e),
                "action": "mindmap_generate_validation_error"
            }
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to generate mindmap",
            extra={
                "user_id": str(user.id),
                "note_id": note_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "action": "mindmap_generate_error"
            }
        )
        raise HTTPException(status_code=500, detail="Failed to generate mindmap")


@router.get("/note/{note_id}")
async def get_mindmap_by_note(
    note_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest mindmap for a note."""
    user, _ = current_user
    
    logger.debug(
        "Fetching mindmap by note ID",
        extra={
            "user_id": str(user.id),
            "note_id": note_id,
            "action": "mindmap_get_by_note"
        }
    )
    
    from app.models.mindmap import Mindmap
    from sqlalchemy import select

    result = await db.execute(
        select(Mindmap)
        .where(Mindmap.note_id == uuid.UUID(note_id))
        .where(Mindmap.user_id == user.id)
        .order_by(Mindmap.version.desc())
        .limit(1)
    )
    mindmap = result.scalar_one_or_none()

    if not mindmap:
        logger.warning(
            "Mindmap not found for note",
            extra={
                "user_id": str(user.id),
                "note_id": note_id,
                "action": "mindmap_not_found"
            }
        )
        raise HTTPException(status_code=404, detail="Mindmap not found")

    logger.info(
        "Mindmap retrieved successfully",
        extra={
            "user_id": str(user.id),
            "note_id": note_id,
            "mindmap_id": str(mindmap.id),
            "version": mindmap.version,
            "action": "mindmap_retrieved"
        }
    )

    return {
        "id": str(mindmap.id),
        "noteId": str(mindmap.note_id),
        "structure": mindmap.structure,
        "aiModel": mindmap.ai_model,
        "mapType": mindmap.map_type,
        "version": mindmap.version,
        "createdAt": mindmap.created_at.isoformat(),
    }


@router.get("/{mindmap_id}")
async def get_mindmap(
    mindmap_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a mindmap by ID."""
    user, _ = current_user
    
    logger.debug(
        "Fetching mindmap by ID",
        extra={
            "user_id": str(user.id),
            "mindmap_id": mindmap_id,
            "action": "mindmap_get_by_id"
        }
    )
    
    mindmap_service = MindmapService(db)
    mindmap = await mindmap_service.get_mindmap(
        mindmap_id=uuid.UUID(mindmap_id),
        user_id=user.id,
    )
    await mindmap_service.close()

    if not mindmap:
        logger.warning(
            "Mindmap not found by ID",
            extra={
                "user_id": str(user.id),
                "mindmap_id": mindmap_id,
                "action": "mindmap_not_found"
            }
        )
        raise HTTPException(status_code=404, detail="Mindmap not found")

    logger.info(
        "Mindmap retrieved by ID",
        extra={
            "user_id": str(user.id),
            "mindmap_id": mindmap_id,
            "version": mindmap.version,
            "action": "mindmap_retrieved"
        }
    )

    return {
        "id": str(mindmap.id),
        "noteId": str(mindmap.note_id),
        "structure": mindmap.structure,
        "aiModel": mindmap.ai_model,
        "mapType": mindmap.map_type,
        "version": mindmap.version,
        "createdAt": mindmap.created_at.isoformat(),
    }


@router.put("/{mindmap_id}")
async def update_mindmap(
    mindmap_id: str,
    structure: dict,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update mindmap structure (e.g., after manual edits)."""
    user, _ = current_user
    
    logger.info(
        "Mindmap update requested",
        extra={
            "user_id": str(user.id),
            "mindmap_id": mindmap_id,
            "action": "mindmap_update_start"
        }
    )
    
    mindmap_service = MindmapService(db)
    
    try:
        updated_mindmap = await mindmap_service.update_mindmap(
            mindmap_id=uuid.UUID(mindmap_id),
            user_id=user.id,
            new_structure=structure,
        )
        await mindmap_service.close()
        
        logger.info(
            "Mindmap updated successfully",
            extra={
                "user_id": str(user.id),
                "mindmap_id": mindmap_id,
                "version": updated_mindmap.version,
                "action": "mindmap_updated"
            }
        )
    except ValueError as e:
        await mindmap_service.close()
        logger.error(
            "Validation error during mindmap update",
            extra={
                "user_id": str(user.id),
                "mindmap_id": mindmap_id,
                "error": str(e),
                "action": "mindmap_update_validation_error"
            }
        )
        raise HTTPException(status_code=400, detail=str(e))

    if not updated_mindmap:
        logger.warning(
            "Mindmap not found for update",
            extra={
                "user_id": str(user.id),
                "mindmap_id": mindmap_id,
                "action": "mindmap_update_not_found"
            }
        )
        raise HTTPException(status_code=404, detail="Mindmap not found")

    return {
        "id": str(updated_mindmap.id),
        "noteId": str(updated_mindmap.note_id),
        "structure": updated_mindmap.structure,
        "aiModel": updated_mindmap.ai_model,
        "mapType": updated_mindmap.map_type,
        "version": updated_mindmap.version,
        "createdAt": updated_mindmap.created_at.isoformat(),
    }


@router.delete("/{mindmap_id}", status_code=204)
async def delete_mindmap(
    mindmap_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a mindmap."""
    user, _ = current_user
    
    logger.info(
        "Mindmap deletion requested",
        extra={
            "user_id": str(user.id),
            "mindmap_id": mindmap_id,
            "action": "mindmap_delete_start"
        }
    )
    
    mindmap_service = MindmapService(db)
    success = await mindmap_service.delete_mindmap(
        mindmap_id=uuid.UUID(mindmap_id),
        user_id=user.id,
    )
    await mindmap_service.close()

    if not success:
        logger.warning(
            "Mindmap not found for deletion",
            extra={
                "user_id": str(user.id),
                "mindmap_id": mindmap_id,
                "action": "mindmap_delete_not_found"
            }
        )
        raise HTTPException(status_code=404, detail="Mindmap not found")
    
    logger.info(
        "Mindmap deleted successfully",
        extra={
            "user_id": str(user.id),
            "mindmap_id": mindmap_id,
            "action": "mindmap_deleted"
        }
    )


@router.get("/{mindmap_id}/versions")
async def get_mindmap_versions(
    mindmap_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all versions of a mindmap."""
    user, _ = current_user
    mindmap_service = MindmapService(db)
    versions = await mindmap_service.get_mindmap_versions(
        mindmap_id=uuid.UUID(mindmap_id),
        user_id=user.id,
    )
    await mindmap_service.close()

    return {
        "versions": [
            {
                "id": str(v.id),
                "noteId": str(v.note_id),
                "version": v.version,
                "mapType": v.map_type,
                "aiModel": v.ai_model,
                "createdAt": v.created_at.isoformat(),
            }
            for v in versions
        ]
    }


@router.get("/{mindmap_id}/knowledge-points")
async def get_knowledge_points(
    mindmap_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge points extracted from a mindmap."""
    user, _ = current_user
    mindmap_service = MindmapService(db)
    
    try:
        points = await mindmap_service.get_knowledge_points(
            mindmap_id=uuid.UUID(mindmap_id),
            user_id=user.id,
        )
        await mindmap_service.close()
    except ValueError as e:
        await mindmap_service.close()
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "knowledgePoints": [
            {
                "id": str(p.id),
                "nodeId": p.node_id,
                "nodePath": p.node_path,
                "text": p.text,
                "level": p.level,
                "parentNode": p.parent_node_id,
                "description": p.description,
                "keywords": p.keywords,
            }
            for p in points
        ]
    }
