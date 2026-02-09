"""Category models."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, Decimal
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    """Category model."""

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)

    # Hierarchy
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=0)  # 0=root, 1=subcategory...

    # Statistics
    notes_count = Column(Integer, default=0)
    children_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    notes = relationship("Note", back_populates="category")
    parent = relationship("Category", remote_side=[id], foreign_keys=[parent_id])

    # Constraints
    __table_args__ = (UniqueConstraint("user_id", "name", "parent_id", name="uq_user_name_parent"),)

    def __repr__(self):
        return f"<Category {self.name}>"


class CategoryRelation(Base):
    """Category relation model."""

    __tablename__ = "category_relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    category_a_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    category_b_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    # Relation type
    relation_type = Column(String(20), nullable=False)  # related, independent

    # Weight (for calculating association strength)
    weight = Column(Decimal(3, 2), default=0.5)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Constraints
    __table_args__ = (
        UniqueConstraint("category_a_id", "category_b_id", name="uq_category_pair"),
        CheckConstraint("category_a_id < category_b_id", name="check_ordered_pair"),
    )

    def __repr__(self):
        return f"<CategoryRelation {self.category_a_id}-{self.category_b_id}>"
