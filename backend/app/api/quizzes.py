"""Quiz management routes - comprehensive API for quiz generation, CRUD, and grading."""

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.quiz import Quiz, QuizQuestion, QuizSession, QuizAnswer
from app.schemas.quiz import (
    AnswerResultResponse,
    QuestionResponse,
    QuestionWithAnswerResponse,
    QuizDeleteResponse,
    QuizDetailResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizListResponse,
    QuizSessionResponse,
    QuizStatsResponse,
    QuizUpdateRequest,
    QuizUpdateResponse,
)
from app.services.quiz_generation_service import QuizGenerationService
from app.services.quiz_grading_service import QuizGradingService

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])


# ============================================================================
# Generation Endpoints
# ============================================================================


@router.post("/generate/{mindmap_id}", response_model=QuizGenerateResponse)
async def generate_quiz(
    mindmap_id: uuid.UUID,
    request: QuizGenerateRequest,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizGenerateResponse:
    """Generate quiz from mindmap using AI.

    Args:
        mindmap_id: Mindmap ID to generate quiz from
        request: Quiz generation parameters
        current_user: Authenticated user
        db: Database session

    Returns:
        Generated quiz information

    Raises:
        HTTPException: If generation fails
    """
    user, _ = current_user

    try:
        service = QuizGenerationService(db)
        quiz = await service.generate_quiz(
            mindmap_id=mindmap_id,
            user_id=user.id,
            question_count=request.question_count,
            question_types=request.question_types,
            difficulty=request.difficulty,
        )
        await service.close()

        logger.info(f"Generated quiz {quiz.id} for user {user.id}")

        return QuizGenerateResponse(
            quiz_id=quiz.id,
            status=quiz.status,
            total_questions=quiz.question_count,
            message="Quiz generated successfully",
        )

    except ValueError as e:
        logger.error(f"Quiz generation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error generating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz. Please try again.",
        )


# ============================================================================
# CRUD Endpoints
# ============================================================================


@router.get("", response_model=QuizListResponse)
async def list_quizzes(
    skip: int = Query(0, ge=0, description="Number of quizzes to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of quizzes to return"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    difficulty_filter: Optional[str] = Query(None, description="Filter by difficulty"),
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizListResponse:
    """List all quizzes for current user with pagination and filtering.

    Args:
        skip: Number of records to skip
        limit: Number of records to return
        status_filter: Optional status filter
        difficulty_filter: Optional difficulty filter
        current_user: Authenticated user
        db: Database session

    Returns:
        Paginated list of quizzes
    """
    user, _ = current_user

    # Build query
    query = select(Quiz).where(Quiz.user_id == user.id)

    if status_filter:
        query = query.where(Quiz.status == status_filter)

    if difficulty_filter:
        query = query.where(Quiz.difficulty == difficulty_filter)

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Quiz.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    quizzes = result.scalars().all()

    return QuizListResponse(
        quizzes=[
            {
                "id": str(q.id),
                "mindmapId": str(q.mindmap_id),
                "questionCount": q.question_count,
                "difficulty": q.difficulty,
                "questionTypes": q.question_types,
                "status": q.status,
                "createdAt": q.created_at.isoformat(),
                "completedAt": q.completed_at.isoformat() if q.completed_at else None,
            }
            for q in quizzes
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{quiz_id}", response_model=QuizDetailResponse)
async def get_quiz(
    quiz_id: uuid.UUID,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizDetailResponse:
    """Get quiz details with questions (without answers).

    Args:
        quiz_id: Quiz ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Quiz details with questions

    Raises:
        HTTPException: If quiz not found or unauthorized
    """
    user, _ = current_user

    # Get quiz
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id, Quiz.user_id == user.id)
        .options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    return QuizDetailResponse(
        id=quiz.id,
        mindmap_id=quiz.mindmap_id,
        user_id=quiz.user_id,
        question_count=quiz.question_count,
        difficulty=quiz.difficulty,
        question_types=quiz.question_types,
        status=quiz.status,
        created_at=quiz.created_at.isoformat(),
        completed_at=quiz.completed_at.isoformat() if quiz.completed_at else None,
        questions=[
            QuestionResponse(
                id=q.id,
                knowledge_point_id=q.knowledge_point_id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                difficulty=q.difficulty,
                order=q.order,
            )
            for q in sorted(quiz.questions, key=lambda x: x.order)
        ],
    )


@router.patch("/{quiz_id}", response_model=QuizUpdateResponse)
async def update_quiz(
    quiz_id: uuid.UUID,
    request: QuizUpdateRequest,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizUpdateResponse:
    """Update quiz metadata.

    Args:
        quiz_id: Quiz ID
        request: Update data
        current_user: Authenticated user
        db: Database session

    Returns:
        Update confirmation

    Raises:
        HTTPException: If quiz not found or unauthorized
    """
    user, _ = current_user

    # Get quiz
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id)
    )
    quiz = result.scalar_one_or_none()

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    # Update fields
    if request.difficulty is not None:
        quiz.difficulty = request.difficulty

    await db.commit()
    await db.refresh(quiz)

    logger.info(f"Updated quiz {quiz_id} for user {user.id}")

    return QuizUpdateResponse(
        quiz_id=quiz.id,
        updated=True,
        message="Quiz updated successfully",
    )


@router.delete("/{quiz_id}", response_model=QuizDeleteResponse)
async def delete_quiz(
    quiz_id: uuid.UUID,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizDeleteResponse:
    """Delete a quiz and all associated data.

    Args:
        quiz_id: Quiz ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Deletion confirmation

    Raises:
        HTTPException: If quiz not found or unauthorized
    """
    user, _ = current_user

    # Get quiz
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id)
    )
    quiz = result.scalar_one_or_none()

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    # Delete quiz (cascade will handle questions, sessions, answers)
    await db.delete(quiz)
    await db.commit()

    logger.info(f"Deleted quiz {quiz_id} for user {user.id}")

    return QuizDeleteResponse(
        quiz_id=quiz_id,
        deleted=True,
        message="Quiz deleted successfully",
    )


# ============================================================================
# Submission and Grading Endpoints
# ============================================================================


@router.post("/{quiz_id}/submit", response_model=QuizSessionResponse)
async def submit_quiz_answers(
    quiz_id: uuid.UUID,
    request: SubmitAnswersRequest,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizSessionResponse:
    """Submit quiz answers for AI grading.

    Args:
        quiz_id: Quiz ID
        request: Answers to submit
        current_user: Authenticated user
        db: Database session

    Returns:
        Quiz session with grading results

    Raises:
        HTTPException: If submission fails
    """
    user, _ = current_user

    try:
        # Initialize grading service
        grading_service = QuizGradingService(db)
        await grading_service.initialize()

        # Convert answers to dict format
        answers_data = [
            {"question_id": ans.question_id, "user_answer": ans.user_answer}
            for ans in request.answers
        ]

        # Submit and grade
        session = await grading_service.submit_answers(
            quiz_id=quiz_id,
            user_id=user.id,
            answers=answers_data,
        )

        await grading_service.close()

        # Get answers for response
        await db.refresh(session, attribute_names=["answers"])

        logger.info(f"Graded quiz {quiz_id} for user {user.id}, score: {session.score:.2f}")

        return QuizSessionResponse(
            id=session.id,
            quiz_id=session.quiz_id,
            status=session.status,
            total_questions=session.total_questions,
            correct_count=session.correct_count,
            score=session.score,
            started_at=session.started_at.isoformat(),
            completed_at=session.completed_at.isoformat() if session.completed_at else None,
            answers=[
                AnswerResultResponse(
                    question_id=ans.question_id,
                    user_answer=ans.user_answer,
                    is_correct=ans.is_correct == "true" or ans.is_correct is True,
                    ai_score=ans.ai_score,
                    ai_feedback=ans.ai_feedback,
                    note_snippets=ans.note_snippets,
                )
                for ans in session.answers
            ],
        )

    except ValueError as e:
        logger.error(f"Answer submission validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Unexpected error submitting answers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit answers. Please try again.",
        )


@router.get("/sessions/{session_id}", response_model=QuizSessionResponse)
async def get_quiz_session(
    session_id: uuid.UUID,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizSessionResponse:
    """Get quiz session results.

    Args:
        session_id: Session ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Quiz session with results

    Raises:
        HTTPException: If session not found or unauthorized
    """
    user, _ = current_user

    grading_service = QuizGradingService(db)
    await grading_service.initialize()

    session = await grading_service.get_session_results(session_id, user.id)

    await grading_service.close()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.refresh(session, attribute_names=["answers"])

    return QuizSessionResponse(
        id=session.id,
        quiz_id=session.quiz_id,
        status=session.status,
        total_questions=session.total_questions,
        correct_count=session.correct_count,
        score=session.score,
        started_at=session.started_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
        answers=[
            AnswerResultResponse(
                question_id=ans.question_id,
                user_answer=ans.user_answer,
                is_correct=ans.is_correct == "true" or ans.is_correct is True,
                ai_score=ans.ai_score,
                ai_feedback=ans.ai_feedback,
                note_snippets=ans.note_snippets,
            )
            for ans in session.answers
        ],
    )


@router.get("/{quiz_id}/review", response_model=QuizDetailResponse)
async def get_quiz_review(
    quiz_id: uuid.UUID,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizDetailResponse:
    """Get quiz with correct answers for review.

    Args:
        quiz_id: Quiz ID
        current_user: Authenticated user
        db: Database session

    Returns:
        Quiz details with correct answers

    Raises:
        HTTPException: If quiz not found or unauthorized
    """
    user, _ = current_user

    # Get quiz
    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == quiz_id, Quiz.user_id == user.id)
        .options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()

    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    # Return with answers
    return QuizDetailResponse(
        id=quiz.id,
        mindmap_id=quiz.mindmap_id,
        user_id=quiz.user_id,
        question_count=quiz.question_count,
        difficulty=quiz.difficulty,
        question_types=quiz.question_types,
        status=quiz.status,
        created_at=quiz.created_at.isoformat(),
        completed_at=quiz.completed_at.isoformat() if quiz.completed_at else None,
        questions=[
            QuestionResponse(
                id=q.id,
                knowledge_point_id=q.knowledge_point_id,
                question_text=q.question_text,
                question_type=q.question_type,
                options=q.options,
                difficulty=q.difficulty,
                order=q.order,
            )
            for q in sorted(quiz.questions, key=lambda x: x.order)
        ],
    )


# ============================================================================
# Statistics Endpoint
# ============================================================================


@router.get("/stats/overview", response_model=QuizStatsResponse)
async def get_quiz_stats(
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> QuizStatsResponse:
    """Get quiz statistics for current user.

    Args:
        current_user: Authenticated user
        db: Database session

    Returns:
        Quiz statistics
    """
    user, _ = current_user

    # Total quizzes
    total_result = await db.execute(
        select(func.count()).select_from(Quiz).where(Quiz.user_id == user.id)
    )
    total_quizzes = total_result.scalar() or 0

    # Completed quizzes
    completed_result = await db.execute(
        select(func.count())
        .select_from(Quiz)
        .where(Quiz.user_id == user.id, Quiz.status == "completed")
    )
    completed_quizzes = completed_result.scalar() or 0

    # Get all sessions for score calculation
    from sqlalchemy import func

    sessions_result = await db.execute(
        select(QuizSession.score, QuizSession.correct_count, QuizSession.total_questions).where(
            QuizSession.user_id == user.id, QuizSession.status == "completed"
        )
    )
    sessions = sessions_result.all()

    if sessions:
        average_score = sum(s.score for s in sessions) / len(sessions)
        total_questions = sum(s.total_questions for s in sessions)
        total_correct = sum(s.correct_count for s in sessions)
        correct_rate = total_correct / total_questions if total_questions > 0 else 0
    else:
        average_score = 0.0
        total_questions = 0
        correct_rate = 0.0

    return QuizStatsResponse(
        total_quizzes=total_quizzes,
        completed_quizzes=completed_quizzes,
        average_score=round(average_score, 2),
        total_questions_answered=total_questions,
        correct_answers_rate=round(correct_rate, 2),
    )

    user, _ = current_user
    from app.models.quiz import Quiz
    from sqlalchemy import select

    result = await db.execute(
        select(Quiz)
        .where(Quiz.user_id == user.id)
        .order_by(Quiz.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    quizzes = result.scalars().all()

    return {
        "quizzes": [
            {
                "id": str(q.id),
                "noteId": str(q.note_id),
                "title": q.title,
                "questionCount": q.question_count,
                "createdAt": q.created_at.isoformat(),
            }
            for q in quizzes
        ],
        "total": len(quizzes),
    }
