"""Note schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class NoteBase(BaseModel):
    """Base note schema."""

    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=100000)
    category_id: Optional[UUID] = None
    tags: list[str] = Field(default_factory=list, max_length=50)


class NoteCreate(NoteBase):
    """Note creation schema."""

    file_url: Optional[str] = Field(None, max_length=2000)
    thumbnail_url: Optional[str] = Field(None, max_length=2000)
    ocr_text: Optional[str] = Field(None, max_length=100000)
    meta_data: dict = Field(default_factory=dict)


class NoteUpdate(BaseModel):
    """Note update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=100000)
    category_id: Optional[UUID] = None
    tags: Optional[list[str]] = Field(None, max_length=50)
    meta_data: Optional[dict] = None


class NoteResponse(BaseModel):
    """Note response schema."""

    id: UUID
    user_id: UUID
    title: str
    content: Optional[str] = None
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ocr_text: Optional[str] = None
    category_id: Optional[UUID] = None
    tags: list[str]
    meta_data: dict
    is_favorited: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class NoteListResponse(BaseModel):
    """Note list response schema."""

    notes: list[NoteResponse]
    total: int
    page: int
    limit: int


class NoteUploadResponse(BaseModel):
    """Note upload response schema."""

    note: NoteResponse
    ocr_confidence: Optional[float] = None
    file_size: int
    content_type: str


class OCRResponse(BaseModel):
    """OCR recognition response schema."""

    text: str
    confidence: Optional[float] = None
