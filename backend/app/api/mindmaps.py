"""Mindmap management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.services.mindmap_service import mindmap_service
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

        # Generate mindmap using DeepSeek
        deepseek = DeepSeekService()
        mindmap_structure = await deepseek.generate_mindmap(
            note_content=note.content or note.ocr_text or "",
            note_title=note.title,
            max_levels=max_levels,
        )
        await deepseek.close()

        # Save mindmap to database
        from app.models.mindmap import Mindmap

        new_mindmap = Mindmap(
            user_id=user.id,
            note_id=uuid.UUID(note_id),
            structure=mindmap_structure,
            ai_model="deepseek-chat",
            version=1,
        )
        db.add(new_mindmap)
        await db.commit()
        await db.refresh(new_mindmap)

        return {
            "id": str(new_mindmap.id),
            "noteId": str(new_mindmap.note_id),
            "structure": new_mindmap.structure,
            "aiModel": new_mindmap.ai_model,
            "version": new_mindmap.version,
            "createdAt": new_mindmap.created_at.isoformat(),
        }
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
    from app.models.mindmap import Mindmap
    from sqlalchemy import select

    result = await db.execute(
        select(Mindmap)
        .where(Mindmap.id == uuid.UUID(mindmap_id))
        .where(Mindmap.user_id == user.id)
    )
    mindmap = result.scalar_one_or_none()

    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")

    return {
        "id": str(mindmap.id),
        "noteId": str(mindmap.note_id),
        "structure": mindmap.structure,
        "aiModel": mindmap.ai_model,
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
    from app.models.mindmap import Mindmap
    from sqlalchemy import select

    result = await db.execute(
        select(Mindmap)
        .where(Mindmap.id == uuid.UUID(mindmap_id))
        .where(Mindmap.user_id == user.id)
    )
    mindmap = result.scalar_one_or_none()

    if not mindmap:
        raise HTTPException(status_code=404, detail="Mindmap not found")

    # Increment version
    mindmap.version += 1
    mindmap.structure = structure
    await db.commit()
    await db.refresh(mindmap)

    return {
        "id": str(mindmap.id),
        "noteId": str(mindmap.note_id),
        "structure": mindmap.structure,
        "aiModel": mindmap.ai_model,
        "version": mindmap.version,
        "createdAt": mindmap.created_at.isoformat(),
    }
