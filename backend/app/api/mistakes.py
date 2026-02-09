"""Mistake (错题) management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.schemas.mistake import (
    MistakeCreate,
    MistakeListResponse,
    MistakeResponse,
    MistakeUpdate,
    ReviewRecord,
    ReviewResponse,
    WeakPointAnalysis,
    WeakPointReport,
)
from app.services.mistake_service import MistakeService

router = APIRouter(prefix="/api/mistakes", tags=["Mistakes"])


@router.post("", response_model=MistakeResponse, status_code=status.HTTP_201_CREATED)
async def create_mistake(
    mistake_data: MistakeCreate,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new mistake record.

    Args:
        mistake_data: Mistake creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created mistake
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    mistake = await mistake_service.create_mistake(user.id, mistake_data)

    return MistakeResponse.model_validate(mistake)


@router.get("", response_model=MistakeListResponse)
async def get_mistakes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    subject: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    is_archived: Optional[bool] = None,
    review_due: Optional[bool] = None,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mistakes for current user with pagination and filters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        subject: Filter by subject
        knowledge_point: Filter by knowledge point
        is_archived: Filter by archived status
        review_due: Only show mistakes due for review
        current_user: Current authenticated user
        db: Database session

    Returns:
        Paginated list of mistakes
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    mistakes, total = await mistake_service.get_mistakes(
        user_id=user.id,
        skip=skip,
        limit=limit,
        subject=subject,
        knowledge_point=knowledge_point,
        is_archived=is_archived,
        review_due=review_due,
    )

    return MistakeListResponse(
        mistakes=[MistakeResponse.model_validate(m) for m in mistakes],
        total=total,
        page=skip // limit + 1,
        limit=limit,
    )


@router.get("/weak-points", response_model=WeakPointReport)
async def get_weak_points(
    limit: int = Query(10, ge=1, le=50),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get weak knowledge points analysis.

    Args:
        limit: Maximum number of weak points to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        Weak point analysis report
    """
    from datetime import datetime

    user, _ = current_user

    mistake_service = MistakeService(db)
    weak_points_data = await mistake_service.analyze_weak_points(user.id, limit)

    weak_points = [WeakPointAnalysis(**wp) for wp in weak_points_data]

    # Get total mistakes count
    _, total = await mistake_service.get_mistakes(user_id=user.id, is_archived=False)

    # Count unique subjects
    subjects = set(wp.subject for wp in weak_points)

    return WeakPointReport(
        weak_points=weak_points,
        total_mistakes=total,
        subjects_count=len(subjects),
        generated_at=datetime.utcnow(),
    )


@router.get("/due-count")
async def get_due_review_count(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get count of mistakes due for review.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Count of mistakes due for review
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    count = await mistake_service.get_due_review_count(user.id)

    return {"due_count": count}


@router.get("/{mistake_id}", response_model=MistakeResponse)
async def get_mistake(
    mistake_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific mistake by ID.

    Args:
        mistake_id: Mistake ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Mistake details

    Raises:
        HTTPException: If mistake not found
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    mistake = await mistake_service.get_mistake(uuid.UUID(mistake_id), user.id)

    if not mistake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mistake not found",
        )

    return MistakeResponse.model_validate(mistake)


@router.put("/{mistake_id}", response_model=MistakeResponse)
async def update_mistake(
    mistake_id: str,
    mistake_data: MistakeUpdate,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a mistake.

    Args:
        mistake_id: Mistake ID
        mistake_data: Mistake update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated mistake

    Raises:
        HTTPException: If mistake not found
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    mistake = await mistake_service.update_mistake(
        uuid.UUID(mistake_id), user.id, mistake_data
    )

    if not mistake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mistake not found",
        )

    return MistakeResponse.model_validate(mistake)


@router.delete("/{mistake_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mistake(
    mistake_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a mistake.

    Args:
        mistake_id: Mistake ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If mistake not found
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    success = await mistake_service.delete_mistake(uuid.UUID(mistake_id), user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mistake not found",
        )


@router.post("/{mistake_id}/review", response_model=ReviewResponse)
async def review_mistake(
    mistake_id: str,
    review_data: ReviewRecord,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Record a mistake review and update mastery.

    Args:
        mistake_id: Mistake ID
        review_data: Review record data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated mistake with new review schedule

    Raises:
        HTTPException: If mistake not found
    """
    user, _ = current_user

    mistake_service = MistakeService(db)
    mistake = await mistake_service.review_mistake(
        uuid.UUID(mistake_id), user.id, review_data
    )

    if not mistake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mistake not found",
        )

    return ReviewResponse(
        mistake=MistakeResponse.model_validate(mistake),
        is_correct=review_data.is_correct,
        mastery_level=mistake.mastery_level,
        next_review_at=mistake.next_review_at,
    )
