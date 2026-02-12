"""Mistake models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


class Mistake(Base):
    """Mistake model."""

    __tablename__ = "mistakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=True)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)

    # Question content (snapshot, prevents modification issues)
    question = Column(Text, nullable=False)  # Changed from question_text to match schema
    question_type = Column(String(20), nullable=False)
    options = Column(JSON, nullable=True)  # JSON instead of JSONB for SQLite compatibility
    correct_answer = Column(Text, nullable=False)

    # User's wrong answer
    user_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    # Tags and categories
    subject = Column(String(100), nullable=False)  # Added for categorization
    knowledge_points = Column(JSON, nullable=True, default=list)  # Changed from knowledge_point_id to array
    tags = Column(JSON, nullable=True, default=list)
    difficulty = Column(Integer, nullable=False, default=1)
    source = Column(String(200), nullable=True)

    # Related note (for context)
    related_note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="SET NULL"), nullable=True)

    # Mastery and review tracking
    mastery_level = Column(Integer, default=0)  # 0-100
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    incorrect_count = Column(Integer, default=0)
    consecutive_correct = Column(Integer, default=0)
    last_review_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Archive support
    is_archived = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    reviews = relationship("MistakeReview", back_populates="mistake", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Mistake {self.id}>"


class MistakeReview(Base):
    """Mistake review model."""

    __tablename__ = "mistake_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mistake_id = Column(UUID(as_uuid=True), ForeignKey("mistakes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Review result
    is_correct = Column(Boolean, nullable=False)
    review_time = Column(Integer, nullable=True)  # seconds

    # Ebbinghaus forgetting curve
    review_stage = Column(Integer, default=0)  # 0-6 (7 review stages)
    next_review_at = Column(DateTime, nullable=True)

    reviewed_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mistake = relationship("Mistake", back_populates="reviews")

    def __repr__(self):
        return f"<MistakeReview {self.id}>"
