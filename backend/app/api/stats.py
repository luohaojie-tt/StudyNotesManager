"""Enhanced Analytics API routes with caching."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.schemas.analytics import (
    OverviewResponse,
    OverviewStats,
    RecentActivity,
    PerformanceResponse,
    PerformanceTrend,
    KnowledgeAreaStats,
    MistakesResponse,
    MistakeTopic,
    MistakeCategory,
    ReviewRecommendation,
    StudyTimeResponse,
    StudyTimeByCategory,
    DailyStudyPattern,
)
from app.services.enhanced_analytics_service import AnalyticsService

router = APIRouter(prefix="/api/stats", tags=["Statistics"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's learning overview statistics.

    Returns overview stats including total notes, quizzes, mistakes,
    accuracy rate, study streak, and recent activity.
    """
    user, _ = current_user

    analytics_service = AnalyticsService(db)
    overview_data = await analytics_service.get_overview(user.id)

    return OverviewResponse(
        stats=OverviewStats(**overview_data["stats"]),
        recent_activity=overview_data.get("recent_activity", []),
    )


@router.get("/notes", response_model=dict)
async def get_notes_statistics(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    days: int = Query(30, ge=1, le=90),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get notes statistics with trends.

    Returns total notes, storage usage, and daily upload trends.
    """
    user, _ = current_user

    analytics_service = AnalyticsService(db)
    notes_data = await analytics_service.get_notes_stats(user.id, days=days)

    return {
        "total_notes": notes_data["total_notes"],
        "total_storage_mb": notes_data["total_storage_mb"],
        "upload_trends": notes_data["upload_trends"],
    }


@router.get("/quizzes", response_model=dict)
async def get_quiz_performance(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    days: int = Query(30, ge=1, le=90),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get quiz performance statistics.

    Returns average score, completion rate, and daily trends.
    """
    user, _ = current_user

    analytics_service = AnalyticsService(db)
    quiz_data = await analytics_service.get_quiz_performance(user.id, days=days)

    return {
        "total_quizzes": quiz_data["total_quizzes"],
        "average_score": quiz_data["average_score"],
        "completion_rate": quiz_data["completion_rate"],
        "daily_trends": quiz_data["daily_trends"],
    }


@router.get("/mistakes", response_model=dict)
async def get_mistake_statistics(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get mistake statistics and weak points.

    Returns total mistakes, mastery distribution, and top weak areas.
    """
    user, _ = current_user

    analytics_service = AnalyticsService(db)
    mistake_data = await analytics_service.get_mistake_patterns(user.id)

    return {
        "total_mistakes": mistake_data["total_mistakes"],
        "mastery_distribution": mistake_data["mastery_distribution"],
        "weak_knowledge_points": mistake_data["weak_knowledge_points"],
    }


@router.get("/timeline", response_model=dict)
async def get_learning_timeline(
    days: int = Query(30, ge=7, le=90),
    group_by: str = Query("day", regex="^(day|week)$"),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get learning timeline with daily/weekly activity.

    Returns activity metrics grouped by day or week.
    """
    user, _ = current_user

    analytics_service = AnalyticsService(db)
    timeline_data = await analytics_service.get_learning_timeline(user.id, days=days, group_by=group_by)

    return timeline_data
