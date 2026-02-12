"""Note model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Numeric, Boolean, JSON, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    # Fallback if pgvector not installed - use LargeBinary for embeddings
    HAS_PGVECTOR = False
    Vector = None
from sqlalchemy.orm import relationship

from app.core.database import Base


class Note(Base):
    """Note model."""

    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Note content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    file_type = Column(String(20), nullable=False)  # image, pdf, handwriting, text
    file_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    # OCR results
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Numeric(3, 2), nullable=True)

    # Vector embedding - use LargeBinary for SQLite compatibility
    # Note: pgvector's Vector type doesn't work with SQLite, so we store as binary
    embedding = Column(LargeBinary, nullable=True)

    # Category
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Tags
    # Use JSON instead of ARRAY for SQLite compatibility
    tags = Column(JSON, default=list)

    # Favorite
    is_favorited = Column(Boolean, default=False)

    # Statistics
    view_count = Column(Integer, default=0)
    mindmap_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata (use meta_data to avoid SQLAlchemy reserved word)
    # Use JSON instead of JSONB for SQLite compatibility
    meta_data = Column(JSON, default=dict)

    # Relationships
    user = relationship("User", back_populates="notes")
    category = relationship("Category", back_populates="notes")
    mindmaps = relationship("Mindmap", back_populates="note", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Note {self.title}>"
