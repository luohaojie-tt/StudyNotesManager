"""Mindmap API routers."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.mindmap_service import MindmapService


router = APIRouter(prefix="/api/mindmaps", tags=["mindmaps"])


class MindmapGenerateResponse(BaseModel):
    """Response for mindmap generation request."""

    task_id: uuid.UUID
    status: str
    message: str


class MindmapResponse(BaseModel):
    """Mindmap response."""

    id: uuid.UUID
    note_id: uuid.UUID
    structure: Dict[str, Any]
    map_type: str
    ai_model: str | None
    ai_generated_at: str | None
    version: int
    is_public: bool
    created_at: str
    updated_at: str


class MindmapUpdateRequest(BaseModel):
    """Request to update mindmap."""

    structure: Dict[str, Any] = Field(..., description="New mindmap structure")


@router.post("/generate/{note_id}", response_model=MindmapGenerateResponse)
async def generate_mindmap(
    note_id: uuid.UUID,
    user_id: uuid.UUID,
    note_content: str,
    note_title: str,
    db: AsyncSession = Depends(get_db),
) -> MindmapGenerateResponse:
    """Generate mindmap from note content.

    Args:
        note_id: Note ID
        user_id: User ID
        note_content: Note text content
        note_title: Note title
        db: Database session

    Returns:
        Task ID for tracking generation

    Raises:
        HTTPException: If generation fails
    """
    try:
        service = MindmapService(db)

        # Generate mindmap
        mindmap = await service.generate_mindmap(
            note_id=note_id,
            user_id=user_id,
            note_content=note_content,
            note_title=note_title,
        )

        await service.close()

        return MindmapGenerateResponse(
            task_id=mindmap.id,
            status="completed",
            message="Mindmap generated successfully",
        )

    except ValueError as e:
        logger.error(f"Mindmap generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mindmap",
        )


@router.get("/{mindmap_id}", response_model=MindmapResponse)
async def get_mindmap(
    mindmap_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MindmapResponse:
    """Get mindmap by ID.

    Args:
        mindmap_id: Mindmap ID
        user_id: User ID
        db: Database session

    Returns:
        Mindmap data

    Raises:
        HTTPException: If mindmap not found
    """
    service = MindmapService(db)
    mindmap = await service.get_mindmap(mindmap_id, user_id)
    await service.close()

    if not mindmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mindmap not found",
        )

    return MindmapResponse(
        id=mindmap.id,
        note_id=mindmap.note_id,
        structure=mindmap.structure,
        map_type=mindmap.map_type,
        ai_model=mindmap.ai_model,
        ai_generated_at=mindmap.ai_generated_at.isoformat() if mindmap.ai_generated_at else None,
        version=mindmap.version,
        is_public=mindmap.is_public,
        created_at=mindmap.created_at.isoformat(),
        updated_at=mindmap.updated_at.isoformat(),
    )


@router.put("/{mindmap_id}", response_model=MindmapResponse)
async def update_mindmap(
    mindmap_id: uuid.UUID,
    user_id: uuid.UUID,
    update_data: MindmapUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> MindmapResponse:
    """Update mindmap structure.

    Args:
        mindmap_id: Mindmap ID
        user_id: User ID
        update_data: Update data
        db: Database session

    Returns:
        Updated mindmap

    Raises:
        HTTPException: If update fails
    """
    try:
        service = MindmapService(db)
        mindmap = await service.update_mindmap(
            mindmap_id=mindmap_id,
            user_id=user_id,
            new_structure=update_data.structure,
        )
        await service.close()

        if not mindmap:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mindmap not found",
            )

        return MindmapResponse(
            id=mindmap.id,
            note_id=mindmap.note_id,
            structure=mindmap.structure,
            map_type=mindmap.map_type,
            ai_model=mindmap.ai_model,
            ai_generated_at=mindmap.ai_generated_at.isoformat() if mindmap.ai_generated_at else None,
            version=mindmap.version,
            is_public=mindmap.is_public,
            created_at=mindmap.created_at.isoformat(),
            updated_at=mindmap.updated_at.isoformat(),
        )

    except ValueError as e:
        logger.error(f"Mindmap update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error updating mindmap: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update mindmap",
        )


@router.get("/{mindmap_id}/versions", response_model=List[MindmapResponse])
async def get_mindmap_versions(
    mindmap_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> List[MindmapResponse]:
    """Get all versions of a mindmap.

    Args:
        mindmap_id: Original mindmap ID
        user_id: User ID
        db: Database session

    Returns:
        List of mindmap versions
    """
    service = MindmapService(db)
    versions = await service.get_mindmap_versions(mindmap_id, user_id)
    await service.close()

    return [
        MindmapResponse(
            id=m.id,
            note_id=m.note_id,
            structure=m.structure,
            map_type=m.map_type,
            ai_model=m.ai_model,
            ai_generated_at=m.ai_generated_at.isoformat() if m.ai_generated_at else None,
            version=m.version,
            is_public=m.is_public,
            created_at=m.created_at.isoformat(),
            updated_at=m.updated_at.isoformat(),
        )
        for m in versions
    ]


@router.delete("/{mindmap_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mindmap(
    mindmap_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete mindmap.

    Args:
        mindmap_id: Mindmap ID
        user_id: User ID
        db: Database session

    Raises:
        HTTPException: If mindmap not found
    """
    service = MindmapService(db)
    deleted = await service.delete_mindmap(mindmap_id, user_id)
    await service.close()

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mindmap not found",
        )
