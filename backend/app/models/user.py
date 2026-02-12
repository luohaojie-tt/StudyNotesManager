"""User model."""
import uuid
from datetime import datetime

from sqlalchemy import VARCHAR, Boolean, Column, DateTime, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base



class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))

    # Subscription information
    subscription_tier = Column(
        VARCHAR(20), default="free"
    )  # free, pro, team
    subscription_expires_at = Column(DateTime, nullable=True)

    # OAuth (optional)
    oauth_provider = Column(String(50), nullable=True)
    oauth_id = Column(String(255), nullable=True)

    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)

    # Metadata (using user_data to avoid SQLAlchemy reserved word)
    # Use JSON instead of JSONB for SQLite compatibility
    user_data = Column(JSON, default=dict)

    # Relationships
    notes = relationship("Note", back_populates="user")
    mindmaps = relationship("Mindmap", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")
    mistakes = relationship("Mistake", back_populates="user")
    categories = relationship("Category", back_populates="user")
    note_shares = relationship("NoteShare", back_populates="user")

    def __repr__(self):
        return f"<User {self.email}>"
