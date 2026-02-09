"""Share and study session models."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class NoteShare(Base):
    """Note share model."""

    __tablename__ = "note_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Share configuration
    share_id = Column(String(20), unique=True, nullable=False, index=True)
    access_type = Column(String(20), default="public")  # public, password, restricted
    password_hash = Column(String(255), nullable=True)

    # Permissions
    allow_download = Column(Boolean, default=True)
    allow_merge = Column(Boolean, default=True)

    # Statistics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    merge_count = Column(Integer, default=0)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    note = relationship("Note")
    user = relationship("User")

    def __repr__(self):
        return f"<NoteShare {self.share_id}>"


class StudySession(Base):
    """Study session model."""

    __tablename__ = "study_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Session info
    session_type = Column(String(20), nullable=False)  # note_reading, quiz_practice, mistake_review
    related_note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id"), nullable=True)
    related_quiz_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id"), nullable=True)

    # Duration
    duration_seconds = Column(Integer, nullable=False)

    # Data statistics
    questions_answered = Column(Integer, default=0)
    questions_correct = Column(Integer, default=0)
    notes_created = Column(Integer, default=0)

    # Time
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
    related_note = relationship("Note", foreign_keys=[related_note_id])
    related_quiz = relationship("QuizQuestion", foreign_keys=[related_quiz_id])

    def __repr__(self):
        return f"<StudySession {self.session_type}>"
