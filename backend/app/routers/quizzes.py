"""Quiz API routers."""

import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.quiz_generation_service import QuizGenerationService
from app.services.quiz_grading_service import QuizGradingService


router = APIRouter(prefix="/api/quizzes", tags=["quizzes"])


class QuizGenerateRequest(BaseModel):
    """Request to generate quiz."""

    question_count: int = Field(default=10, ge=1, le=50)
    question_types: List[str] = Field(default=["choice", "fill_blank"])
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class QuizGenerateResponse(BaseModel):
    """Response for quiz generation."""

    quiz_id: uuid.UUID
    status: str
    total_questions: int


class QuestionResponse(BaseModel):
    """Quiz question response."""

    id: uuid.UUID
    knowledge_point_id: uuid.UUID | None
    question_text: str
    question_type: str
    options: List[str] | None
    difficulty: str


class QuizDetailResponse(BaseModel):
    """Quiz detail response."""

    id: uuid.UUID
    mindmap_id: uuid.UUID
    questions: List[QuestionResponse]
    created_at: str


class SubmitAnswerRequest(BaseModel):
    """Answer submission request."""

    question_id: uuid.UUID
    user_answer: str


class SubmitAnswersRequest(BaseModel):
    """Multiple answers submission request."""

    answers: List[SubmitAnswerRequest]


class QuizSessionResponse(BaseModel):
    """Quiz session response."""

    id: uuid.UUID
    quiz_id: uuid.UUID
    status: str
    total_questions: int
    correct_count: int
    score: float
    started_at: str
    completed_at: str | None


@router.post("/generate/{mindmap_id}", response_model=QuizGenerateResponse)
async def generate_quiz(
    mindmap_id: uuid.UUID,
    user_id: uuid.UUID,
    request: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> QuizGenerateResponse:
    """Generate quiz from mindmap.

    Args:
        mindmap_id: Mindmap ID
        user_id: User ID
        request: Quiz generation parameters
        db: Database session

    Returns:
        Quiz generation response

    Raises:
        HTTPException: If generation fails
    """
    try:
        service = QuizGenerationService(db)
        quiz = await service.generate_quiz(
            mindmap_id=mindmap_id,
            user_id=user_id,
            question_count=request.question_count,
            question_types=request.question_types,
            difficulty=request.difficulty,
        )
        await service.close()

        return QuizGenerateResponse(
            quiz_id=quiz.id,
            status=quiz.status,
            total_questions=quiz.question_count,
        )

    except ValueError as e:
        logger.error(f"Quiz generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz",
        )


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz(
    quiz_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> QuizDetailResponse:
    """Get quiz details with questions.

    Args:
        quiz_id: Quiz ID
        user_id: User ID
        db: Database session

    Returns:
        Quiz details

    Raises:
        HTTPException: If quiz not found
    """
    try:
        service = QuizGenerationService(db)
        questions = await service.get_quiz_questions(quiz_id, user_id)
        await service.close()

        return QuizDetailResponse(
            id=quiz_id,
            mindmap_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # Placeholder
            questions=[
                QuestionResponse(
                    id=q.id,
                    knowledge_point_id=q.knowledge_point_id,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    options=q.options,
                    difficulty=q.difficulty,
                )
                for q in questions
            ],
            created_at="2026-02-08T10:30:00Z",  # Placeholder
        )

    except ValueError as e:
        logger.error(f"Failed to get quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error getting quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quiz",
        )


@router.post("/{quiz_id}/answer", response_model=QuizSessionResponse)
async def submit_quiz_answers(
    quiz_id: uuid.UUID,
    user_id: uuid.UUID,
    request: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
) -> QuizSessionResponse:
    """Submit quiz answers for grading.

    Args:
        quiz_id: Quiz ID
        user_id: User ID
        request: Answers to submit
        db: Database session

    Returns:
        Quiz session with results

    Raises:
        HTTPException: If submission fails
    """
    try:
        # Initialize grading service with vector search
        grading_service = QuizGradingService(db)
        await grading_service.initialize()

        # Convert answers to dict format
        answers_data = [
            {"question_id": ans.question_id, "user_answer": ans.user_answer}
            for ans in request.answers
        ]

        session = await grading_service.submit_answers(
            quiz_id=quiz_id,
            user_id=user_id,
            answers=answers_data,
        )

        await grading_service.close()

        return QuizSessionResponse(
            id=session.id,
            quiz_id=session.quiz_id,
            status=session.status,
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            score=session.score,
            started_at=session.started_at.isoformat(),
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
        )

    except ValueError as e:
        logger.error(f"Answer submission failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error submitting answers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answers",
        )


@router.get("/sessions/{session_id}", response_model=QuizSessionResponse)
async def get_quiz_session(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> QuizSessionResponse:
    """Get quiz session results.

    Args:
        session_id: Session ID
        user_id: User ID
        db: Database session

    Returns:
        Quiz session with results

    Raises:
        HTTPException: If session not found
    """
    try:
        grading_service = QuizGradingService(db)
        await grading_service.initialize()

        session = await grading_service.get_session_results(session_id, user_id)

        await grading_service.close()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        return QuizSessionResponse(
            id=session.id,
            quiz_id=session.quiz_id,
            status=session.status,
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            score=session.score,
            started_at=session.started_at.isoformat(),
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session",
        )
