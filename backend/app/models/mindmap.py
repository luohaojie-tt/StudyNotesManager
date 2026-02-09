"""Mindmap database models."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Mindmap(Base):
    """Mindmap model."""

    __tablename__ = "mindmaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id = Column(UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Mindmap structure
    structure = Column(JSON, nullable=False)
    map_type = Column(String(50), nullable=False, default="ai_generated")  # ai_generated, manual

    # AI metadata
    ai_model = Column(String(100), nullable=True)
    ai_generated_at = Column(DateTime(timezone=True), nullable=True)

    # Version control
    version = Column(Integer, nullable=False, default=1)
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("mindmaps.id"), nullable=True)

    # Visibility
    is_public = Column(Text, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="mindmaps")
    note = relationship("Note", back_populates="mindmaps")
    knowledge_points = relationship("KnowledgePoint", back_populates="mindmap", cascade="all, delete-orphan")
    parent_version = relationship("Mindmap", remote_side=[id], backref="child_versions")


class KnowledgePoint(Base):
    """Knowledge point extracted from mindmap."""

    __tablename__ = "mindmap_knowledge_points"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mindmap_id = Column(UUID(as_uuid=True), ForeignKey("mindmaps.id", ondelete="CASCADE"), nullable=False, index=True)

    # Node information
    node_id = Column(String(100), nullable=False)  # ID from mindmap structure
    node_path = Column(Text, nullable=False)  # Path like "root/node1/node1-1"
    text = Column(Text, nullable=False)

    # Hierarchy
    level = Column(Integer, nullable=False)
    parent_node_id = Column(String(100), nullable=True)

    # Metadata
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # Array of keywords

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    mindmap = relationship("Mindmap", back_populates="knowledge_points")
    quiz_questions = relationship("QuizQuestion", back_populates="knowledge_point")
