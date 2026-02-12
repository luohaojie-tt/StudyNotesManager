"""Quiz database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Float, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base


class Quiz(Base):
    """Quiz model."""

    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mindmap_id = Column(UUID(as_uuid=True), ForeignKey("mindmaps.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Quiz configuration
    question_count = Column(Integer, nullable=False)
    difficulty = Column(Enum("easy", "medium", "hard", name="quiz_difficulty"), default="medium")
    # Use JSON instead of ARRAY for SQLite compatibility
    question_types = Column(JSON, nullable=False)  # ["choice", "fill_blank", "short_answer"]

    # Status
    status = Column(Enum("generating", "ready", "completed", name="quiz_status"), default="generating")

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    mindmap = relationship("Mindmap")
    user = relationship("User")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    sessions = relationship("QuizSession", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    """Quiz question model."""

    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    knowledge_point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mindmap_knowledge_points.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Question content
    question_text = Column(Text, nullable=False)
    question_type = Column(Enum("choice", "fill_blank", "short_answer", name="question_type"), nullable=False)
    options = Column(JSON, nullable=True)  # For choice questions: ["A. option1", "B. option2", ...]
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)

    # Metadata
    difficulty = Column(Enum("easy", "medium", "hard", name="question_difficulty"), default="medium")
    order = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    knowledge_point = relationship("KnowledgePoint", back_populates="quiz_questions")
    answers = relationship("QuizAnswer", back_populates="question", cascade="all, delete-orphan")


class QuizSession(Base):
    """Quiz session (user taking a quiz)."""

    __tablename__ = "quiz_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Session status
    status = Column(Enum("in_progress", "completed", name="session_status"), default="in_progress")

    # Results
    total_questions = Column(Integer, nullable=False)
    correct_count = Column(Integer, default=0)
    score = Column(Float, default=0.0)

    # Timestamps
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="sessions")
    user = relationship("User")
    answers = relationship("QuizAnswer", back_populates="session", cascade="all, delete-orphan")


class QuizAnswer(Base):
    """User answer to a quiz question."""

    __tablename__ = "quiz_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Answer
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Text, nullable=False)

    # AI grading for short answers
    ai_score = Column(Float, nullable=True)
    ai_feedback = Column(Text, nullable=True)

    # Related note content (for wrong answers)
    note_snippets = Column(JSON, nullable=True)  # Array of {content, page, similarity}

    # Timestamp
    answered_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("QuizSession", back_populates="answers")
    question = relationship("QuizQuestion", back_populates="answers")
