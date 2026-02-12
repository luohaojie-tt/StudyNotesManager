"""Enhanced Analytics service with full statistics and caching."""
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from sqlalchemy import select, func, and_, desc, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.models.quiz import Quiz, QuizSession, QuizAnswer
from app.models.mistake import Mistake
from app.models.share import StudySession
from app.models.category import Category


# Simple in-memory cache for expensive queries
_cache: Dict[str, tuple[datetime, Any]] = {}
_cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes


def cache_result(ttl_seconds: int = 300):
    """Decorator to cache expensive query results.

    Args:
        ttl_seconds: Time-to-live in seconds (default: 5 minutes)

    Returns:
        Cached result or None
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs
            user_id = kwargs.get('user_id')

            if not user_id:
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = f"{func.__name__}:{user_id}"

            # Check cache
            if cache_key in _cache:
                cached_at, result = _cache[cache_key]
                # Check if cache is still valid
                if datetime.utcnow() - cached_at < timedelta(seconds=ttl_seconds):
                    return result

            # Execute and cache
            result = await func(*args, **kwargs)
            _cache[cache_key] = (datetime.utcnow(), result)

            return result
        return wrapper
    return decorator


class AnalyticsService:
    """Service for learning analytics and insights."""

    def __init__(self, db: AsyncSession):
        """Initialize analytics service.

        Args:
            db: Database session
        """
        self.db = db

    @cache_result(ttl_seconds=300)  # Cache for 5 minutes
    async def get_overview(self, user_id: uuid.UUID) -> dict:
        """Get user's learning overview statistics.

        Args:
            user_id: User ID

        Returns:
            Dictionary with overview stats
        """
        # Get total counts
        notes_result = await self.db.execute(
            select(func.count(Note.id)).where(Note.user_id == user_id)
        )
        total_notes = notes_result.scalar() or 0

        quizzes_result = await self.db.execute(
            select(func.count(Quiz.id)).where(Quiz.user_id == user_id)
        )
        total_quizzes = quizzes_result.scalar() or 0

        mistakes_result = await self.db.execute(
            select(func.count(Mistake.id)).where(Mistake.user_id == user_id)
        )
        total_mistakes = mistakes_result.scalar() or 0

        # Calculate accuracy rate from quiz sessions
        accuracy_result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(QuizSession.correct_count).cast(float) /
                    func.coalesce(func.sum(QuizSession.total_questions), 0),
                    0.0
                )
            ).where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.status == "completed"
                )
            )
        )
        accuracy_rate = accuracy_result.scalar() or 0.0

        # Get study time this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        study_time_result = await self.db.execute(
            select(func.sum(StudySession.duration_seconds))
            .where(
                and_(
                    StudySession.user_id == user_id,
                    StudySession.started_at >= week_ago,
                )
            )
        )
        total_study_seconds = study_time_result.scalar() or 0
        total_study_time_minutes = int(total_study_seconds / 60)

        return {
            "total_notes": total_notes,
            "total_quizzes": total_quizzes,
            "total_mistakes": total_mistakes,
            "accuracy_rate": float(accuracy_rate),
            "study_time_this_week_minutes": total_study_time_minutes,
        }

    @cache_result(ttl_seconds=300)
    async def get_notes_stats(self, user_id: uuid.UUID) -> dict:
        """Get notes statistics with trends.

        Args:
            user_id: User ID

        Returns:
            Notes statistics with daily/weekly trends
        """
        # Total notes
        total_result = await self.db.execute(
            select(func.count(Note.id)).where(Note.user_id == user_id)
        )
        total_notes = total_result.scalar() or 0

        # Storage usage (sum of file sizes)
        storage_result = await self.db.execute(
            select(func.sum(Note.file_size)).where(Note.user_id == user_id)
        )
        total_storage = storage_result.scalar() or 0
        total_storage_mb = round(total_storage / (1024 * 1024), 2)

        # Daily upload trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_uploads = await self.db.execute(
            select(
                func.date(Note.created_at).label("date"),
                func.count(Note.id).label("count"),
            )
            .where(
                and_(
                    Note.user_id == user_id,
                    Note.created_at >= thirty_days_ago,
                )
            )
            .group_by(func.date(Note.created_at))
            .order_by(func.date(Note.created_at))
        )

        upload_trends = []
        for row in daily_uploads.scalars():
            upload_trends.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "count": row.count or 0,
            })

        return {
            "total_notes": total_notes,
            "total_storage_mb": total_storage_mb,
            "upload_trends_30_days": upload_trends,
        }

    @cache_result(ttl_seconds=300)
    async def get_quiz_performance(self, user_id: uuid.UUID) -> dict:
        """Get quiz performance with trends.

        Args:
            user_id: User ID

        Returns:
            Quiz performance statistics
        """
        # Get completed quiz sessions
        result = await self.db.execute(
            select(
                func.count(QuizSession.id).label("total_quizzes"),
                func.avg(QuizSession.score).label("avg_score"),
                func.sum(QuizSession.total_questions).label("total_questions"),
                func.sum(QuizSession.correct_count).label("total_correct"),
            )
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.status == "completed",
                )
            )
        )
        row = result.one()

        total_quizzes = row.total_quizzes or 0
        avg_score = float(row.avg_score or 0.0)
        total_questions = row.total_questions or 0
        total_correct = row.total_correct or 0
        completion_rate = float(total_correct / total_questions) if total_questions > 0 else 0.0

        # Daily trends (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        daily_result = await self.db.execute(
            select(
                func.date(QuizSession.completed_at).label("date"),
                func.avg(QuizSession.score).label("avg_score"),
                func.count(QuizSession.id).label("quiz_count"),
            )
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.status == "completed",
                    QuizSession.completed_at >= thirty_days_ago,
                )
            )
            .group_by(func.date(QuizSession.completed_at))
            .order_by(func.date(QuizSession.completed_at))
        )

        daily_trends = []
        for row in daily_result.scalars():
            daily_trends.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "average_score": float(row.avg_score or 0.0),
                "quiz_count": row.quiz_count or 0,
            })

        return {
            "total_quizzes": total_quizzes,
            "average_score": avg_score,
            "completion_rate": completion_rate,
            "total_questions_answered": total_questions,
            "total_correct": total_correct,
            "daily_trends_30_days": daily_trends,
        }

    @cache_result(ttl_seconds=300)
    async def get_mistake_patterns(self, user_id: uuid.UUID) -> dict:
        """Get mistake patterns and analysis.

        Args:
            user_id: User ID

        Returns:
            Mistake statistics with weak points
        """
        # Get total mistakes
        total_result = await self.db.execute(
            select(func.count(Mistake.id)).where(Mistake.user_id == user_id)
        )
        total_mistakes = total_result.scalar() or 0

        # Mastery distribution
        mastery_result = await self.db.execute(
            select(
                Mistake.mastery_level.label("level"),
                func.count(Mistake.id).label("count"),
            )
            .where(Mistake.user_id == user_id)
            .group_by(Mistake.mastery_level)
            .order_by(Mistake.mastery_level)
        )

        mastery_distribution = []
        for row in mastery_result.scalars():
            level = row.level or 0
            count = row.count or 0
            mastery_distribution.append({
                "level": level,
                "count": count,
                "percentage": round(count / total_mistakes * 100, 1) if total_mistakes > 0 else 0,
            })

        # Weak knowledge points (by subject)
        weak_result = await self.db.execute(
            select(
                Mistake.subject.label("subject"),
                func.count(Mistake.id).label("count"),
                func.avg(Mistake.mastery_level).label("avg_mastery"),
            )
            .where(Mistake.user_id == user_id)
            .group_by(Mistake.subject)
            .order_by(desc("count"))
            .limit(10)
        )

        weak_knowledge_points = []
        for row in weak_result.scalars():
            weak_knowledge_points.append({
                "subject": row.subject,
                "count": row.count or 0,
                "average_mastery": float(row.avg_mastery or 0.0),
            })

        return {
            "total_mistakes": total_mistakes,
            "mastery_distribution": mastery_distribution,
            "weak_knowledge_points": weak_knowledge_points[:5],
        }

    @cache_result(ttl_seconds=300)
    async def get_learning_timeline(self, user_id: uuid.UUID, days: int = 30) -> dict:
        """Get learning timeline with daily/weekly activity.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Timeline data with activity metrics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Get daily activity
        daily_result = await self.db.execute(
            select(
                func.date(StudySession.started_at).label("date"),
                func.sum(StudySession.duration_seconds).label("total_seconds"),
                func.count(StudySession.id).label("session_count"),
                func.sum(case((StudySession.session_type == "note_reading", StudySession.notes_created), else_=0)).label("notes_created"),
                func.sum(case((StudySession.session_type == "quiz_practice", StudySession.questions_answered), else_=0)).label("questions_answered"),
            )
            .where(
                and_(
                    StudySession.user_id == user_id,
                    StudySession.started_at >= start_date,
                )
            )
            .group_by(func.date(StudySession.started_at))
            .order_by(func.date(StudySession.started_at))
        )

        daily_activity = []
        for row in daily_result.scalars():
            daily_activity.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "total_study_minutes": int(row.total_seconds / 60) if row.total_seconds else 0,
                "session_count": row.session_count or 0,
                "notes_created": row.notes_created or 0,
                "questions_answered": row.questions_answered or 0,
            })

        # Calculate weekly totals
        total_sessions = sum(day["session_count"] for day in daily_activity)
        total_study_minutes = sum(day["total_study_minutes"] for day in daily_activity)

        return {
            "daily_activity": daily_activity,
            "summary": {
                "total_sessions": total_sessions,
                "total_study_minutes": total_study_minutes,
                "avg_study_minutes_per_day": int(total_study_minutes / len(daily_activity)) if daily_activity else 0,
            }
        }
