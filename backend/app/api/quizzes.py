"""Quiz management routes."""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.services.quiz_generation_service import quiz_generation_service
from app.services.quiz_grading_service import quiz_grading_service

router = APIRouter(prefix="/api/quizzes", tags=["Quizzes"])


@router.post("/generate/{note_id}")
async def generate_quiz(
    note_id: str,
    count: int = 10,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a quiz from a note using AI."""
    user, _ = current_user
    try:
        # Get note content
        from app.models.note import Note
        from sqlalchemy import select

        result = await db.execute(
            select(Note).where(Note.id == uuid.UUID(note_id)).where(Note.user_id == user.id)
        )
        note = result.scalar_one_or_none()

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        # Generate quiz using AI
        quiz_data = await quiz_generation_service.generate_quiz(
            note_content=note.content or note.ocr_text or "",
            note_title=note.title,
            question_count=count,
        )

        # Save quiz to database
        from app.models.quiz import Quiz, Question

        new_quiz = Quiz(
            user_id=user.id,
            note_id=uuid.UUID(note_id),
            title=f"Quiz: {note.title}",
            question_count=len(quiz_data["questions"]),
        )
        db.add(new_quiz)
        await db.flush()

        # Save questions
        for q_data in quiz_data["questions"]:
            question = Question(
                quiz_id=new_quiz.id,
                question_text=q_data["question"],
                question_type=q_data["type"],
                options=q_data.get("options"),
                correct_answer=q_data["answer"],
                explanation=q_data.get("explanation"),
            )
            db.add(question)

        await db.commit()
        await db.refresh(new_quiz)

        # Load questions
        await db.refresh(new_quiz, ["questions"])

        return {
            "id": str(new_quiz.id),
            "noteId": str(new_quiz.note_id),
            "title": new_quiz.title,
            "questions": [
                {
                    "id": str(q.id),
                    "type": q.question_type,
                    "question": q.question_text,
                    "options": q.options,
                    "correctAnswer": q.correct_answer,
                    "explanation": q.explanation,
                }
                for q in new_quiz.questions
            ],
            "createdAt": new_quiz.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")


@router.get("/{quiz_id}")
async def get_quiz(
    quiz_id: str,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a quiz by ID."""
    user, _ = current_user
    from app.models.quiz import Quiz
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Quiz)
        .where(Quiz.id == uuid.UUID(quiz_id))
        .where(Quiz.user_id == user.id)
        .options(selectinload(Quiz.questions))
    )
    quiz = result.scalar_one_or_none()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return {
        "id": str(quiz.id),
        "noteId": str(quiz.note_id),
        "title": quiz.title,
        "questions": [
            {
                "id": str(q.id),
                "type": q.question_type,
                "question": q.question_text,
                "options": q.options,
                "correctAnswer": q.correct_answer,
                "explanation": q.explanation,
            }
            for q in quiz.questions
        ],
        "createdAt": quiz.created_at.isoformat(),
    }


@router.post("/{quiz_id}/submit")
async def submit_quiz(
    quiz_id: str,
    answers: dict[str, str],
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit quiz answers and get results."""
    user, _ = current_user
    try:
        # Get quiz with questions
        from app.models.quiz import Quiz
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Quiz)
            .where(Quiz.id == uuid.UUID(quiz_id))
            .where(Quiz.user_id == user.id)
            .options(selectinload(Quiz.questions))
        )
        quiz = result.scalar_one_or_none()

        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Grade the quiz
        grading_result = await quiz_grading_service.grade_quiz(
            questions=[
                {
                    "id": str(q.id),
                    "question": q.question_text,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                }
                for q in quiz.questions
            ],
            user_answers=answers,
        )

        # Save attempt
        from app.models.quiz import QuizAttempt

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            user_id=user.id,
            answers=answers,
            score=grading_result["score"],
            total_score=grading_result["total_score"],
        )
        db.add(attempt)
        await db.commit()

        # Create mistakes for wrong answers
        from app.models.mistake import Mistake

        for result in grading_result["question_results"]:
            if not result["is_correct"]:
                mistake = Mistake(
                    user_id=user.id,
                    note_id=quiz.note_id,
                    question_id=result["question_id"],
                    question=result["question"],
                    user_answer=answers.get(result["question_id"]),
                    correct_answer=result["correct_answer"],
                    explanation=result.get("explanation"),
                )
                db.add(mistake)
        await db.commit()

        return {
            "score": grading_result["score"],
            "totalScore": grading_result["total_score"],
            "percentage": grading_result["percentage"],
            "questionResults": grading_result["question_results"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit quiz: {str(e)}")


@router.get("")
async def list_quizzes(
    skip: int = 0,
    limit: int = 20,
    current_user: tuple = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all quizzes for current user."""
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
