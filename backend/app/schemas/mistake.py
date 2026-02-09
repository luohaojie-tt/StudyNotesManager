"""Mistake (错题) schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MistakeBase(BaseModel):
    """Base mistake schema."""

    question: str = Field(..., min_length=1, max_length=2000)
    correct_answer: str = Field(..., min_length=1, max_length=2000)
    user_answer: Optional[str] = Field(None, max_length=2000)
    explanation: Optional[str] = Field(None, max_length=5000)
    question_type: str = Field(default="choice")  # choice, fill_blank, essay
    subject: str = Field(..., min_length=1, max_length=100)
    knowledge_points: list[str] = Field(default_factory=list)
    difficulty: int = Field(default=1, ge=1, le=5)  # 1-5
    source: Optional[str] = Field(None, max_length=200)  # 来源（章节/测验）
    tags: list[str] = Field(default_factory=list)


class MistakeCreate(MistakeBase):
    """Mistake creation schema."""

    quiz_id: Optional[UUID] = None


class MistakeUpdate(BaseModel):
    """Mistake update schema."""

    question: Optional[str] = Field(None, min_length=1, max_length=2000)
    correct_answer: Optional[str] = Field(None, min_length=1, max_length=2000)
    user_answer: Optional[str] = Field(None, max_length=2000)
    explanation: Optional[str] = Field(None, max_length=5000)
    question_type: Optional[str] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    knowledge_points: Optional[list[str]] = None
    difficulty: Optional[int] = Field(None, ge=1, le=5)
    source: Optional[str] = Field(None, max_length=200)
    tags: Optional[list[str]] = None
    is_archived: Optional[bool] = None


class MistakeResponse(BaseModel):
    """Mistake response schema."""

    id: UUID
    user_id: UUID
    question: str
    correct_answer: str
    user_answer: Optional[str]
    explanation: Optional[str]
    question_type: str
    subject: str
    knowledge_points: list[str]
    difficulty: int
    source: Optional[str]
    tags: list[str]
    mastery_level: int  # 0-100
    review_count: int
    correct_count: int
    incorrect_count: int
    last_review_at: Optional[datetime]
    next_review_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""

        from_attributes = True


class MistakeListResponse(BaseModel):
    """Mistake list response schema."""

    mistakes: list[MistakeResponse]
    total: int
    page: int
    limit: int


class ReviewRecord(BaseModel):
    """Review record schema."""

    is_correct: bool
    time_spent: Optional[int] = None  # seconds
    notes: Optional[str] = None


class ReviewResponse(BaseModel):
    """Review response schema."""

    mistake: MistakeResponse
    is_correct: bool
    mastery_level: int
    next_review_at: datetime


class WeakPointAnalysis(BaseModel):
    """Weak point analysis schema."""

    knowledge_point: str
    subject: str
    mistake_count: int
    total_attempts: int
    error_rate: float  # 0.0-1.0
    avg_mastery_level: float
    priority: int  # 1-10, higher is more urgent
    last_mistake_at: Optional[datetime]


class WeakPointReport(BaseModel):
    """Weak point report schema."""

    weak_points: list[WeakPointAnalysis]
    total_mistakes: int
    subjects_count: int
    generated_at: datetime
