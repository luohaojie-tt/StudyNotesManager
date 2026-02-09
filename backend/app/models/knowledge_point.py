"""Mindmap knowledge point model."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Decimal, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, VECTOR
from sqlalchemy.orm import relationship

from app.core.database import Base


class MindmapKnowledgePoint(Base):
    """Mindmap knowledge point model."""

    __tablename__ = "mindmap_knowledge_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mindmap_id = Column(
        UUID(as_uuid=True), ForeignKey("mindmaps.id", ondelete="CASCADE"), nullable=False
    )
    node_id = Column(String(100), nullable=False)  # Node ID in structure JSON

    knowledge_text = Column(Text, nullable=False)
    embedding = Column(VECTOR(1536), nullable=True)

    # Related note content
    related_note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id"), nullable=True)
    related_note_section = Column(String(100), nullable=True)

    # Learning data
    mastery_level = Column(Decimal(3, 2), default=0)  # 0-1
    question_count = Column(Integer, default=0)
    mistake_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mindmap = relationship("Mindmap", back_populates="knowledge_points")
    related_note = relationship("Note", foreign_keys=[related_note_id])

    # Constraints
    __table_args__ = (UniqueConstraint("mindmap_id", "node_id", name="uq_mindmap_node"),)

    def __repr__(self):
        return f"<MindmapKnowledgePoint {self.node_id}>"
