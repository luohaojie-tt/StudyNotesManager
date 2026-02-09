"""Quiz-related Pydantic schemas for request/response validation."""

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Request Schemas


class QuizGenerateRequest(BaseModel):
    """Request to generate quiz from mindmap."""

    question_count: int = Field(default=10, ge=1, le=50, description="Number of questions to generate")
    question_types: List[str] = Field(
        default=["choice", "fill_blank"],
        description="Types of questions: choice, fill_blank, short_answer"
    )
    difficulty: str = Field(
        default="medium",
        pattern="^(easy|medium|hard)$",
        description="Difficulty level: easy, medium, or hard"
    )

    @field_validator("question_types")
    @classmethod
    def validate_question_types(cls, v: List[str]) -> List[str]:
        """Validate question types."""
        valid_types = {"choice", "fill_blank", "short_answer"}
        invalid_types = set(v) - valid_types
        if invalid_types:
            raise ValueError(f"Invalid question types: {invalid_types}. Valid types: {valid_types}")
        if not v:
            raise ValueError("At least one question type must be specified")
        return v


class QuizUpdateRequest(BaseModel):
    """Request to update quiz metadata."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")


class SubmitAnswerRequest(BaseModel):
    """Single answer submission request."""

    question_id: uuid.UUID
    user_answer: str = Field(..., min_length=1, max_length=1000)


class SubmitAnswersRequest(BaseModel):
    """Multiple answers submission request."""

    answers: List[SubmitAnswerRequest]

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: List[SubmitAnswerRequest]) -> List[SubmitAnswerRequest]:
        """Validate answers list."""
        if not v:
            raise ValueError("At least one answer must be provided")
        # Check for duplicate question IDs
        question_ids = [ans.question_id for ans in v]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Duplicate question IDs found")
        return v


class QuizListRequest(BaseModel):
    """Request to list quizzes with pagination."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = Field(None, pattern="^(generating|ready|completed)$")
    difficulty: Optional[str] = Field(None, pattern="^(easy|medium|hard)$")


# Response Schemas


class QuestionResponse(BaseModel):
    """Quiz question response (without correct answer)."""

    id: uuid.UUID
    knowledge_point_id: Optional[uuid.UUID]
    question_text: str
    question_type: str
    options: Optional[List[str]]
    difficulty: str
    order: int


class QuestionWithAnswerResponse(BaseModel):
    """Quiz question response (with correct answer for review)."""

    id: uuid.UUID
    knowledge_point_id: Optional[uuid.UUID]
    question_text: str
    question_type: str
    options: Optional[List[str]]
    correct_answer: str
    explanation: Optional[str]
    difficulty: str
    order: int


class AnswerResultResponse(BaseModel):
    """Single answer result."""

    question_id: uuid.UUID
    user_answer: str
    is_correct: bool
    ai_score: Optional[float]
    ai_feedback: Optional[str]
    note_snippets: Optional[List[Dict[str, Any]]]


class QuizSessionResponse(BaseModel):
    """Quiz session response with results."""

    id: uuid.UUID
    quiz_id: uuid.UUID
    status: str
    total_questions: int
    correct_count: int
    score: float
    started_at: str
    completed_at: Optional[str]
    answers: List[AnswerResultResponse]


class QuizGenerateResponse(BaseModel):
    """Response for quiz generation."""

    quiz_id: uuid.UUID
    status: str
    total_questions: int
    message: str


class QuizDetailResponse(BaseModel):
    """Quiz detail response."""

    id: uuid.UUID
    mindmap_id: uuid.UUID
    user_id: uuid.UUID
    question_count: int
    difficulty: str
    question_types: List[str]
    status: str
    created_at: str
    completed_at: Optional[str]
    questions: List[QuestionResponse]


class QuizListResponse(BaseModel):
    """Response for quiz list."""

    quizzes: List[Dict[str, Any]]
    total: int
    skip: int
    limit: int


class QuizDeleteResponse(BaseModel):
    """Response for quiz deletion."""

    quiz_id: uuid.UUID
    deleted: bool
    message: str


class QuizUpdateResponse(BaseModel):
    """Response for quiz update."""

    quiz_id: uuid.UUID
    updated: bool
    message: str


class QuizStatsResponse(BaseModel):
    """Quiz statistics response."""

    total_quizzes: int
    completed_quizzes: int
    average_score: float
    total_questions_answered: int
    correct_answers_rate: float
