"""Mistake models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Mistake(Base):
    """Mistake model."""

    __tablename__ = "mistakes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=True)

    # Question content (snapshot, prevents modification issues)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)
    options = Column(JSONB, nullable=True)
    correct_answer = Column(Text, nullable=False)

    # User's wrong answer
    user_answer = Column(Text, nullable=False)

    # Tags and categories
    tags = Column(ARRAY(String), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    knowledge_point_id = Column(UUID(as_uuid=True), ForeignKey("mindmap_knowledge_points.id"), nullable=True)

    # Related note
    related_note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id"), nullable=True)
    related_note_snippet = Column(Text, nullable=True)

    # Statistics
    mistake_count = Column(Integer, default=1)
    last_mistake_at = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
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
