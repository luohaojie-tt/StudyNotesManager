"""Analytics API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.schemas.analytics import (
    MistakesResponse,
    OverviewResponse,
    PerformanceResponse,
    StudyTimeResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's learning statistics overview.

    Returns:
        Overview stats including total notes, quizzes, mistakes,
        accuracy rate, study streak, and recent activity.
    """
    user, _ = current_user

    try:
        analytics_service = AnalyticsService(db)
        overview_data = await analytics_service.get_overview(user.id)
        return overview_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve overview statistics: {str(e)}",
        )


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get performance trends and knowledge area analysis.

    Returns:
        Performance trends over time (daily/weekly),
        strong knowledge areas, and weak areas needing improvement.
    """
    user, _ = current_user

    try:
        analytics_service = AnalyticsService(db)
        performance_data = await analytics_service.get_performance(user.id)
        return performance_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance analytics: {str(e)}",
        )


@router.get("/mistakes", response_model=MistakesResponse)
async def get_mistakes_analysis(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mistake analysis and review recommendations.

    Returns:
        Common mistake topics, mistakes by category,
        and prioritized review recommendations.
    """
    user, _ = current_user

    try:
        analytics_service = AnalyticsService(db)
        mistakes_data = await analytics_service.get_mistakes_analysis(user.id)
        return mistakes_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve mistake analytics: {str(e)}",
        )


@router.get("/study-time", response_model=StudyTimeResponse)
async def get_study_time_analytics(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get study time analytics.

    Returns:
        Total study time, time by category,
        and daily study patterns.
    """
    user, _ = current_user

    try:
        analytics_service = AnalyticsService(db)
        study_time_data = await analytics_service.get_study_time(user.id)
        return study_time_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve study time analytics: {str(e)}",
        )
