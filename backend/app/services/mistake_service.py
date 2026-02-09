"""Mistake service for错题库 management and weak point analysis."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mistake import Mistake
from app.schemas.mistake import MistakeCreate, MistakeUpdate, ReviewRecord
from app.utils.ebbinghaus import (
    calculate_mastery_level,
    calculate_next_review,
)


class MistakeService:
    """Service for mistake management and weak point analysis."""

    def __init__(self, db: AsyncSession):
        """Initialize mistake service."""
        self.db = db

    async def create_mistake(self, user_id: uuid.UUID, mistake_data: MistakeCreate) -> Mistake:
        """Create a new mistake record."""
        new_mistake = Mistake(
            user_id=user_id,
            question=mistake_data.question,
            correct_answer=mistake_data.correct_answer,
            user_answer=mistake_data.user_answer,
            explanation=mistake_data.explanation,
            question_type=mistake_data.question_type,
            subject=mistake_data.subject,
            knowledge_points=mistake_data.knowledge_points,
            difficulty=mistake_data.difficulty,
            source=mistake_data.source,
            tags=mistake_data.tags,
            quiz_id=mistake_data.quiz_id,
            mastery_level=0,
            review_count=0,
            correct_count=0,
            incorrect_count=0,
            consecutive_correct=0,
            next_review_at=datetime.utcnow(),
        )

        self.db.add(new_mistake)
        await self.db.commit()
        await self.db.refresh(new_mistake)
        return new_mistake

    async def get_mistake(self, mistake_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Mistake]:
        """Get mistake by ID."""
        result = await self.db.execute(
            select(Mistake)
            .where(Mistake.id == mistake_id)
            .where(Mistake.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_mistakes(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        subject: Optional[str] = None,
        knowledge_point: Optional[str] = None,
        is_archived: Optional[bool] = None,
        review_due: Optional[bool] = None,
    ) -> tuple[list[Mistake], int]:
        """Get mistakes for user with pagination and filters."""
        query = select(Mistake).where(Mistake.user_id == user_id)

        if subject:
            query = query.where(Mistake.subject == subject)
        if knowledge_point:
            query = query.where(Mistake.knowledge_points.contains([knowledge_point]))
        if is_archived is not None:
            query = query.where(Mistake.is_archived == is_archived)
        if review_due:
            query = query.where(Mistake.next_review_at <= datetime.utcnow())

        # Get total count
        count_query = select(func.count(Mistake.id)).where(Mistake.user_id == user_id)
        if subject:
            count_query = count_query.where(Mistake.subject == subject)
        if knowledge_point:
            count_query = count_query.where(Mistake.knowledge_points.contains([knowledge_point]))
        if is_archived is not None:
            count_query = count_query.where(Mistake.is_archived == is_archived)
        if review_due:
            count_query = count_query.where(Mistake.next_review_at <= datetime.utcnow())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        query = query.order_by(Mistake.next_review_at.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        mistakes = result.scalars().all()

        return list(mistakes), total

    async def delete_mistake(self, mistake_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete mistake."""
        mistake = await self.get_mistake(mistake_id, user_id)
        if not mistake:
            return False

        await self.db.delete(mistake)
        await self.db.commit()
        return True

    async def review_mistake(
        self, mistake_id: uuid.UUID, user_id: uuid.UUID, review_data: ReviewRecord
    ) -> Optional[Mistake]:
        """Record a mistake review and update schedule."""
        mistake = await self.get_mistake(mistake_id, user_id)
        if not mistake:
            return None

        # Update review counts
        mistake.review_count += 1
        if review_data.is_correct:
            mistake.correct_count += 1
            mistake.consecutive_correct += 1
        else:
            mistake.incorrect_count += 1
            mistake.consecutive_correct = 0

        # Calculate next review time using Ebbinghaus
        next_review, consecutive = calculate_next_review(
            consecutive_correct=mistake.consecutive_correct,
            is_correct=review_data.is_correct,
            last_review_at=datetime.utcnow(),
        )
        mistake.next_review_at = next_review
        mistake.last_review_at = datetime.utcnow()

        # Calculate mastery level
        mistake.mastery_level = calculate_mastery_level(
            correct_count=mistake.correct_count,
            incorrect_count=mistake.incorrect_count,
            consecutive_correct=mistake.consecutive_correct,
        )

        await self.db.commit()
        await self.db.refresh(mistake)
        return mistake

    async def analyze_weak_points(self, user_id: uuid.UUID, limit: int = 10) -> list[dict]:
        """Analyze user's weak knowledge points."""
        result = await self.db.execute(
            select(Mistake)
            .where(Mistake.user_id == user_id)
            .where(Mistake.is_archived == False)
        )
        mistakes = result.scalars().all()

        # Aggregate by knowledge point
        knowledge_stats = {}

        for mistake in mistakes:
            for kp in mistake.knowledge_points:
                if kp not in knowledge_stats:
                    knowledge_stats[kp] = {
                        "knowledge_point": kp,
                        "subject": mistake.subject,
                        "mistake_count": 0,
                        "total_attempts": 0,
                        "correct_count": 0,
                        "mastery_levels": [],
                        "last_mistake_at": None,
                    }

                stats = knowledge_stats[kp]
                stats["mistake_count"] += 1
                stats["total_attempts"] += mistake.review_count
                stats["correct_count"] += mistake.correct_count
                stats["mastery_levels"].append(mistake.mastery_level)

                if stats["last_mistake_at"] is None or mistake.created_at > stats["last_mistake_at"]:
                    stats["last_mistake_at"] = mistake.created_at

        # Calculate metrics and priority
        weak_points = []
        for kp, stats in knowledge_stats.items():
            error_rate = 1.0 - (stats["correct_count"] / stats["total_attempts"] if stats["total_attempts"] > 0 else 0)
            avg_mastery = sum(stats["mastery_levels"]) / len(stats["mastery_levels"]) if stats["mastery_levels"] else 0

            # Priority: high mistake count + high error rate + low mastery
            priority = int(
                (stats["mistake_count"] * 0.4) + (error_rate * 100 * 0.4) + ((100 - avg_mastery) * 0.2)
            )

            weak_points.append({
                "knowledge_point": kp,
                "subject": stats["subject"],
                "mistake_count": stats["mistake_count"],
                "total_attempts": stats["total_attempts"],
                "error_rate": error_rate,
                "avg_mastery_level": avg_mastery,
                "priority": min(priority, 10),
                "last_mistake_at": stats["last_mistake_at"],
            })

        # Sort by priority (descending) and limit
        weak_points.sort(key=lambda x: x["priority"], reverse=True)
        return weak_points[:limit]

    async def get_due_review_count(self, user_id: uuid.UUID) -> int:
        """Get count of mistakes due for review."""
        result = await self.db.execute(
            select(func.count(Mistake.id))
            .where(Mistake.user_id == user_id)
            .where(Mistake.is_archived == False)
            .where(Mistake.next_review_at <= datetime.utcnow())
        )
        return result.scalar()
