"""Simple statistics service for analytics/stats endpoints.

Provides clean, working aggregations without complex dependencies.
"""
import uuid
from datetime import datetime, timedelta

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.models.quiz import Quiz, QuizSession
from app.models.mistake import Mistake
from app.models.share import StudySession


class StatsService:
    """Service for simple, reliable statistics."""

    def __init__(self, db: AsyncSession):
        """Initialize stats service.

        Args:
            db: Database session
        """
        self.db = db

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
            "total_study_time_minutes": total_study_time_minutes,
        }

    async def get_quiz_stats(self, user_id: uuid.UUID) -> dict:
        """Get quiz performance statistics.

        Args:
            user_id: User ID

        Returns:
            Dictionary with quiz stats
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

        return {
            "total_quizzes": total_quizzes,
            "average_score": avg_score,
            "completion_rate": completion_rate,
            "total_questions_answered": total_questions,
            "total_correct": total_correct,
        }

    async def get_mistake_stats(self, user_id: uuid.UUID) -> dict:
        """Get mistake statistics and weak points.

        Args:
            user_id: User ID

        Returns:
            Dictionary with mistake stats
        """
        # Get total mistakes
        total_result = await self.db.execute(
            select(func.count(Mistake.id)).where(Mistake.user_id == user_id)
        )
        total_mistakes = total_result.scalar() or 0

        # Get mastery distribution
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
            })

        # Get weak knowledge points (group by subject)
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
                "count": row.count,
                "average_mastery": float(row.avg_mastery or 0.0),
            })

        return {
            "total_mistakes": total_mistakes,
            "mastery_distribution": mastery_distribution,
            "weak_knowledge_points": weak_knowledge_points[:5],
        }
