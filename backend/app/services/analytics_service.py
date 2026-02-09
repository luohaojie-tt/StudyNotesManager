"""Analytics service for learning statistics and insights."""
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, and_, desc, case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.note import Note
from app.models.quiz import Quiz, QuizSession, QuizAnswer
from app.models.mistake import Mistake
from app.models.share import StudySession
from app.models.category import Category


class AnalyticsService:
    """Service for analytics and learning insights."""

    def __init__(self, db: AsyncSession):
        """Initialize analytics service.

        Args:
            db: Database session
        """
        self.db = db

    async def get_overview(self, user_id: uuid.UUID) -> dict:
        """Get user's learning overview statistics.

        Args:
            user_id: User ID

        Returns:
            Dictionary with overview stats and recent activity
        """
        # Get total counts
        notes_count_result = await self.db.execute(
            select(func.count(Note.id)).where(Note.user_id == user_id)
        )
        total_notes = notes_count_result.scalar() or 0

        quizzes_count_result = await self.db.execute(
            select(func.count(Quiz.id)).where(Quiz.user_id == user_id)
        )
        total_quizzes = quizzes_count_result.scalar() or 0

        mistakes_count_result = await self.db.execute(
            select(func.count(Mistake.id)).where(Mistake.user_id == user_id)
        )
        total_mistakes = mistakes_count_result.scalar() or 0

        # Calculate accuracy rate from quiz sessions
        accuracy_result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(QuizSession.correct_count).cast(float) /
                    func.nullif(func.sum(QuizSession.total_questions), 0),
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

        # Calculate study streak (consecutive days with activity)
        study_streak = await self._calculate_study_streak(user_id)

        # Get total study time
        study_time_result = await self.db.execute(
            select(
                func.coalesce(func.sum(StudySession.duration_seconds), 0)
            ).where(StudySession.user_id == user_id)
        )
        total_study_seconds = study_time_result.scalar() or 0
        total_study_time_minutes = int(total_study_seconds / 60)

        # Get recent activity (last 7 sessions)
        recent_activity_result = await self.db.execute(
            select(StudySession)
            .where(StudySession.user_id == user_id)
            .order_by(desc(StudySession.started_at))
            .limit(7)
        )
        recent_sessions = recent_activity_result.scalars().all()

        recent_activity = [
            {
                "session_type": session.session_type,
                "duration_seconds": session.duration_seconds,
                "related_note_id": session.related_note_id,
                "started_at": session.started_at,
            }
            for session in recent_sessions
        ]

        return {
            "stats": {
                "total_notes": total_notes,
                "total_quizzes": total_quizzes,
                "total_mistakes": total_mistakes,
                "accuracy_rate": float(accuracy_rate),
                "study_streak": study_streak,
                "total_study_time_minutes": total_study_time_minutes,
            },
            "recent_activity": recent_activity,
        }

    async def get_performance(self, user_id: uuid.UUID) -> dict:
        """Get performance trends and knowledge area analysis.

        Args:
            user_id: User ID

        Returns:
            Dictionary with performance trends and knowledge areas
        """
        # Get daily trends for last 30 days
        daily_trends = await self._get_performance_trends(user_id, days=30, group_by="day")

        # Get weekly trends for last 12 weeks
        weekly_trends = await self._get_performance_trends(user_id, weeks=12, group_by="week")

        # Get knowledge area analysis
        strong_areas, weak_areas = await self._analyze_knowledge_areas(user_id)

        return {
            "daily_trends": daily_trends,
            "weekly_trends": weekly_trends,
            "strong_areas": strong_areas,
            "weak_areas": weak_areas,
        }

    async def get_mistakes_analysis(self, user_id: uuid.UUID) -> dict:
        """Get mistake analysis and review recommendations.

        Args:
            user_id: User ID

        Returns:
            Dictionary with mistake analysis
        """
        # Get total mistakes
        total_result = await self.db.execute(
            select(func.count(Mistake.id)).where(Mistake.user_id == user_id)
        )
        total_mistakes = total_result.scalar() or 0

        # Get common mistake topics (from knowledge_point tags or question_text)
        common_topics_result = await self.db.execute(
            select(
                Mistake.question_text.label("topic"),
                func.count(Mistake.id).label("count"),
            )
            .where(Mistake.user_id == user_id)
            .group_by(Mistake.question_text)
            .order_by(desc("count"))
            .limit(10)
        )

        common_topics = []
        for row in common_topics_result:
            # Extract topic from question (simplified - could be improved with NLP)
            topic = row.topic[:100]  # First 100 chars as topic identifier
            common_topics.append({
                "topic": topic,
                "count": row.count,
                "error_rate": 1.0,  # All mistakes are errors
                "avg_mastery_level": 50.0,  # Default for new mistakes
            })

        # Get mistakes by category
        category_joins = await self.db.execute(
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.count(Mistake.id).label("count"),
            )
            .outerjoin(Mistake, Category.id == Mistake.category_id)
            .where(Category.user_id == user_id)
            .group_by(Category.id, Category.name)
            .order_by(desc("count"))
        )

        by_category = []
        for row in category_joins:
            total = row.count or 0
            by_category.append({
                "category_id": row.category_id,
                "category_name": row.category_name,
                "count": total,
                "error_rate": 1.0 if total > 0 else 0.0,
            })

        # Get review recommendations (mistakes with low mastery or high frequency)
        recommendations_result = await self.db.execute(
            select(Mistake)
            .where(Mistake.user_id == user_id)
            .order_by(desc(Mistake.mistake_count), desc(Mistake.last_mistake_at))
            .limit(20)
        )

        review_recommendations = []
        for idx, mistake in enumerate(recommendations_result.scalars()):
            # Calculate priority based on mistake count and recency
            days_since_last = (datetime.utcnow() - mistake.last_mistake_at).days
            priority = min(10, mistake.mistake_count * 2 + max(0, 5 - days_since_last))

            review_recommendations.append({
                "mistake_id": mistake.id,
                "question": mistake.question_text,
                "subject": "General",  # Could be derived from tags
                "mastery_level": 50,  # Default - could be stored in model
                "mistake_count": mistake.mistake_count,
                "last_mistake_at": mistake.last_mistake_at,
                "priority": priority,
            })

        return {
            "total_mistakes": total_mistakes,
            "common_topics": common_topics,
            "by_category": by_category,
            "review_recommendations": review_recommendations,
        }

    async def get_study_time(self, user_id: uuid.UUID) -> dict:
        """Get study time analytics.

        Args:
            user_id: User ID

        Returns:
            Dictionary with study time analysis
        """
        # Get total study time
        total_result = await self.db.execute(
            select(
                func.sum(StudySession.duration_seconds).label("total_seconds"),
                func.count(StudySession.id).label("total_sessions"),
            ).where(StudySession.user_id == user_id)
        )
        row = total_result.one()

        total_study_seconds = row.total_seconds or 0
        total_sessions = row.total_sessions or 0
        avg_session_duration = (
            float(total_study_seconds / total_sessions / 60)
            if total_sessions > 0
            else 0.0
        )

        # Get study time by category (through notes)
        category_time_result = await self.db.execute(
            select(
                Category.id.label("category_id"),
                Category.name.label("category_name"),
                func.coalesce(func.sum(StudySession.duration_seconds), 0).label("total_seconds"),
                func.count(StudySession.id).label("session_count"),
            )
            .outerjoin(Note, Category.id == Note.category_id)
            .outerjoin(
                StudySession,
                and_(
                    StudySession.related_note_id == Note.id,
                    StudySession.user_id == user_id,
                ),
            )
            .where(Category.user_id == user_id)
            .group_by(Category.id, Category.name)
            .order_by(desc("total_seconds"))
        )

        by_category = []
        for row in category_time_result:
            by_category.append({
                "category_id": row.category_id,
                "category_name": row.category_name,
                "total_minutes": int(row.total_seconds / 60) if row.total_seconds else 0,
                "session_count": row.session_count or 0,
            })

        # Get daily study patterns for last 30 days
        daily_patterns = await self._get_daily_study_patterns(user_id, days=30)

        return {
            "total_study_time_minutes": int(total_study_seconds / 60),
            "total_sessions": total_sessions,
            "avg_session_duration_minutes": avg_session_duration,
            "by_category": by_category,
            "daily_patterns": daily_patterns,
        }

    async def _calculate_study_streak(self, user_id: uuid.UUID) -> int:
        """Calculate consecutive study days.

        Args:
            user_id: User ID

        Returns:
            Number of consecutive days with study activity
        """
        # Get all study dates
        result = await self.db.execute(
            select(func.date(StudySession.started_at).label("study_date"))
            .where(StudySession.user_id == user_id)
            .group_by(func.date(StudySession.started_at))
            .order_by(desc("study_date"))
        )
        dates = [row[0] for row in result]

        if not dates:
            return 0

        # Calculate streak
        streak = 0
        current_date = datetime.utcnow().date()

        for study_date in dates:
            if study_date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif study_date == current_date - timedelta(days=1):
                streak += 1
                current_date = study_date - timedelta(days=1)
            else:
                break

        return streak

    async def _get_performance_trends(
        self, user_id: uuid.UUID, days: Optional[int] = None, weeks: Optional[int] = None, group_by: str = "day"
    ) -> list[dict]:
        """Get performance trends over time.

        Args:
            user_id: User ID
            days: Number of days to look back (for daily trends)
            weeks: Number of weeks to look back (for weekly trends)
            group_by: How to group data ("day" or "week")

        Returns:
            List of trend data points
        """
        if group_by == "day" and days:
            start_date = datetime.utcnow() - timedelta(days=days)
            date_trunc = func.date_trunc("day", QuizSession.completed_at)
        elif group_by == "week" and weeks:
            start_date = datetime.utcnow() - timedelta(weeks=weeks)
            date_trunc = func.date_trunc("week", QuizSession.completed_at)
        else:
            return []

        result = await self.db.execute(
            select(
                date_trunc.label("date"),
                func.coalesce(
                    func.avg(QuizSession.score).cast(float),
                    0.0
                ).label("score"),
                func.count(QuizSession.id).label("quiz_count"),
                func.sum(QuizSession.total_questions).label("questions_answered"),
            )
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.status == "completed",
                    QuizSession.completed_at >= start_date,
                )
            )
            .group_by(date_trunc)
            .order_by(date_trunc)
        )

        trends = []
        for row in result:
            trends.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "score": float(row.score or 0.0),
                "quiz_count": row.quiz_count,
                "questions_answered": row.questions_answered or 0,
            })

        return trends

    async def _analyze_knowledge_areas(self, user_id: uuid.UUID) -> tuple[list[dict], list[dict]]:
        """Analyze strong and weak knowledge areas.

        Args:
            user_id: User ID

        Returns:
            Tuple of (strong_areas, weak_areas)
        """
        # Get performance by question type/difficulty
        # This is a simplified version - could be enhanced with knowledge point analysis

        result = await self.db.execute(
            select(
                QuizQuestion.difficulty.label("area"),
                func.count(QuizAnswer.id).label("total_questions"),
                func.sum(case((QuizAnswer.is_correct == True, 1), else_=0)).label("correct_questions"),
            )
            .join(QuizSession, QuizAnswer.session_id == QuizSession.id)
            .join(QuizQuestion, QuizAnswer.question_id == QuizQuestion.id)
            .where(QuizSession.user_id == user_id)
            .group_by(QuizQuestion.difficulty)
        )

        areas = []
        for row in result:
            total = row.total_questions or 0
            correct = row.correct_questions or 0
            accuracy = float(correct / total) if total > 0 else 0.0

            areas.append({
                "area": row.difficulty,
                "total_questions": total,
                "correct_questions": correct,
                "accuracy_rate": accuracy,
                "avg_mastery_level": int(accuracy * 100),
            })

        # Sort by accuracy and split into strong/weak
        sorted_areas = sorted(areas, key=lambda x: x["accuracy_rate"], reverse=True)
        mid_point = len(sorted_areas) // 2

        strong_areas = sorted_areas[:mid_point]
        weak_areas = sorted_areas[mid_point:]

        return strong_areas, weak_areas

    async def _get_daily_study_patterns(self, user_id: uuid.UUID, days: int = 30) -> list[dict]:
        """Get daily study patterns.

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of daily study pattern data
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(
                func.date(StudySession.started_at).label("date"),
                func.sum(StudySession.duration_seconds).label("total_seconds"),
                func.count(StudySession.id).label("session_count"),
                func.sum(
                    case((StudySession.session_type == "note_reading", StudySession.notes_created), else_=0)
                ).label("notes_created"),
                func.sum(
                    case((StudySession.session_type == "quiz_practice", StudySession.quizzes_completed), else_=0)
                ).label("quizzes_completed"),
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

        patterns = []
        for row in result:
            patterns.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "total_minutes": int(row.total_seconds / 60) if row.total_seconds else 0,
                "session_count": row.session_count or 0,
                "notes_created": row.notes_created or 0,
                "quizzes_completed": row.quizzes_completed or 0,
            })

        return patterns
