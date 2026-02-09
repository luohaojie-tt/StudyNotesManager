"""Analytics schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OverviewStats(BaseModel):
    """Overview statistics schema."""

    total_notes: int
    total_quizzes: int
    total_mistakes: int
    accuracy_rate: float  # 0.0-1.0
    study_streak: int  # consecutive days
    total_study_time_minutes: int


class RecentActivity(BaseModel):
    """Recent activity schema."""

    session_type: str
    duration_seconds: int
    related_note_id: Optional[UUID] = None
    started_at: datetime


class OverviewResponse(BaseModel):
    """Overview analytics response schema."""

    stats: OverviewStats
    recent_activity: list[RecentActivity]


class PerformanceTrend(BaseModel):
    """Performance trend data point."""

    date: str  # ISO date string
    score: float
    quiz_count: int
    questions_answered: int


class KnowledgeAreaStats(BaseModel):
    """Knowledge area statistics."""

    area: str
    total_questions: int
    correct_questions: int
    accuracy_rate: float
    avg_mastery_level: float


class PerformanceResponse(BaseModel):
    """Performance analytics response schema."""

    daily_trends: list[PerformanceTrend]
    weekly_trends: list[PerformanceTrend]
    strong_areas: list[KnowledgeAreaStats]
    weak_areas: list[KnowledgeAreaStats]


class MistakeTopic(BaseModel):
    """Mistake by topic schema."""

    topic: str
    count: int
    error_rate: float
    avg_mastery_level: float


class MistakeCategory(BaseModel):
    """Mistake by category schema."""

    category_id: Optional[UUID]
    category_name: Optional[str]
    count: int
    error_rate: float


class ReviewRecommendation(BaseModel):
    """Review recommendation schema."""

    mistake_id: UUID
    question: str
    subject: str
    mastery_level: int
    mistake_count: int
    last_mistake_at: datetime
    priority: int  # 1-10


class MistakesResponse(BaseModel):
    """Mistake analytics response schema."""

    total_mistakes: int
    common_topics: list[MistakeTopic]
    by_category: list[MistakeCategory]
    review_recommendations: list[ReviewRecommendation]


class StudyTimeByCategory(BaseModel):
    """Study time by category schema."""

    category_id: Optional[UUID]
    category_name: Optional[str]
    total_minutes: int
    session_count: int


class DailyStudyPattern(BaseModel):
    """Daily study pattern schema."""

    date: str  # ISO date string
    total_minutes: int
    session_count: int
    notes_created: int
    quizzes_completed: int


class StudyTimeResponse(BaseModel):
    """Study time analytics response schema."""

    total_study_time_minutes: int
    total_sessions: int
    avg_session_duration_minutes: float
    by_category: list[StudyTimeByCategory]
    daily_patterns: list[DailyStudyPattern]
