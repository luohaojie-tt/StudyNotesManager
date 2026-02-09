"""Note model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import JSONB, UUID
try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback if pgvector not installed
    from sqlalchemy import ARRAY
    Vector = ARRAY
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

    # Vector embedding
    embedding = Column(Vector(1536), nullable=True)

    # Category
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)

    # Statistics
    view_count = Column(Integer, default=0)
    mindmap_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Metadata
    metadata = Column(JSONB, default=dict)

    # Relationships
    user = relationship("User", back_populates="notes")
    category = relationship("Category", back_populates="notes")
    mindmaps = relationship("Mindmap", back_populates="note", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Note {self.title}>"
