"""Mindmap management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.services.mindmap_service import MindmapService
from app.services.deepseek_service import DeepSeekService

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
    # Validate max_levels parameter
    if not 1 <= max_levels <= 10:
        raise HTTPException(
            status_code=400,
            detail="max_levels must be between 1 and 10"
        )
    
    user, _ = current_user
    try:
        # Get note content
        from app.models.note import Note
        from sqlalchemy import select

        result = await db.execute(
            select(Note).where(Note.id == uuid.UUID(note_id)).where(Note.user_id == user.id)
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        # Generate mindmap using MindmapService
        mindmap_service = MindmapService(db)
        mindmap = await mindmap_service.generate_mindmap(
            note_id=uuid.UUID(note_id),
            user_id=user.id,
            note_content=note.content or note.ocr_text or "",
            note_title=note.title,
        )
        await mindmap_service.close()

        return {
            "id": str(mindmap.id),
            "noteId": str(mindmap.note_id),
            "structure": mindmap.structure,
            "aiModel": mindmap.ai_model,
            "version": mindmap.version,
            "createdAt": mindmap.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate mindmap: {str(e)}")


@router.get("/note/{note_id}")
async def get_mindmap_by_note(
    note_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest mindmap for a note."""
    user, _ = current_user
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
        raise HTTPException(status_code=404, detail="Mindmap not found")

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
    mindmap_service = MindmapService(db)
    mindmap = await mindmap_service.get_mindmap(
        mindmap_id=uuid.UUID(mindmap_id),
        user_id=user.id,
    )
    await mindmap_service.close()

    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")

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
    mindmap_service = MindmapService(db)
    
    try:
        updated_mindmap = await mindmap_service.update_mindmap(
            mindmap_id=uuid.UUID(mindmap_id),
            user_id=user.id,
            new_structure=structure,
        )
        await mindmap_service.close()
    except ValueError as e:
        await mindmap_service.close()
        raise HTTPException(status_code=400, detail=str(e))

    if not updated_mindmap:
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
    mindmap_service = MindmapService(db)
    success = await mindmap_service.delete_mindmap(
        mindmap_id=uuid.UUID(mindmap_id),
        user_id=user.id,
    )
    await mindmap_service.close()

    if not success:
        raise HTTPException(status_code=404, detail="Mindmap not found")


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
