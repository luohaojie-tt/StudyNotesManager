"""Quiz answer validation and grading service."""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz, QuizSession, QuizAnswer, QuizQuestion
from app.services.deepseek_service import DeepSeekService
from app.services.vector_search_service import VectorSearchService


class QuizGradingService:
    """Service for grading quiz answers."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize grading service.

        Args:
            db: Database session
        """
        self.db = db
        self.deepseek = DeepSeekService()
        self.vector_search = VectorSearchService()

    async def initialize(self) -> None:
        """Initialize vector search service."""
        await self.vector_search.initialize()

    async def submit_answers(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
        answers: List[Dict[str, Any]],
    ) -> QuizSession:
        """Submit and grade quiz answers.

        Args:
            quiz_id: Quiz ID
            user_id: User ID
            answers: List of {question_id, user_answer}

        Returns:
            Quiz session with results

        Raises:
            ValueError: If quiz not found or invalid answers
        """
        # Get quiz
        quiz = await self._get_quiz(quiz_id, user_id)
        if not quiz:
            raise ValueError("Quiz not found or unauthorized")

        # Get all questions
        questions = await self._get_quiz_questions(quiz_id)
        question_dict = {str(q.id): q for q in questions}

        # Create session
        session = QuizSession(
            id=uuid.uuid4(),
            quiz_id=quiz_id,
            user_id=user_id,
            status="in_progress",
            total_questions=len(questions),
            correct_count=0,
            score=0.0,
        )

        self.db.add(session)
        await self.db.flush()

        # Process each answer
        correct_count = 0
        total_score = 0.0

        for answer_data in answers:
            question_id = answer_data.get("question_id")
            user_answer = answer_data.get("user_answer")

            if not question_id or user_answer is None:
                logger.warning(f"Invalid answer data: {answer_data}")
                continue

            question = question_dict.get(str(question_id))
            if not question:
                logger.warning(f"Question {question_id} not found")
                continue

            # Grade answer
            grading_result = await self._grade_answer(question, user_answer, quiz_id)

            # Create answer record
            answer = QuizAnswer(
                id=uuid.uuid4(),
                session_id=session.id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=grading_result["is_correct"],
                ai_score=grading_result.get("ai_score"),
                ai_feedback=grading_result.get("feedback"),
                note_snippets=grading_result.get("note_snippets"),
            )

            self.db.add(answer)

            # Update statistics
            if grading_result["is_correct"]:
                correct_count += 1
                total_score += 1.0
            elif grading_result.get("ai_score"):
                total_score += grading_result["ai_score"]

        # Update session
        session.correct_count = correct_count
        session.score = total_score / len(questions) if questions else 0.0
        session.status = "completed"

        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Graded quiz session {session.id}: score={session.score:.2f}")
        return session

    async def _get_quiz(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Quiz]:
        """Get quiz by ID.

        Args:
            quiz_id: Quiz ID
            user_id: User ID

        Returns:
            Quiz if found, None otherwise
        """
        result = await self.db.execute(
            select(Quiz).where(
                Quiz.id == quiz_id,
                Quiz.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_quiz_questions(
        self,
        quiz_id: uuid.UUID,
    ) -> List[QuizQuestion]:
        """Get all questions for a quiz.

        Args:
            quiz_id: Quiz ID

        Returns:
            List of questions
        """
        result = await self.db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order)
        )
        return list(result.scalars().all())

    async def _grade_answer(
        self,
        question: QuizQuestion,
        user_answer: str,
        quiz_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Grade a single answer.

        Args:
            question: Quiz question
            user_answer: User's answer
            quiz_id: Quiz ID

        Returns:
            Grading result with is_correct, score, feedback, note_snippets
        """
        question_type = question.question_type
        correct_answer = question.correct_answer

        try:
            if question_type == "choice":
                return await self._grade_choice_answer(
                    user_answer, correct_answer
                )

            elif question_type == "fill_blank":
                return await self._grade_fill_blank_answer(
                    user_answer, correct_answer
                )

            elif question_type == "short_answer":
                return await self._grade_short_answer(
                    question, user_answer, correct_answer, quiz_id
                )

            else:
                logger.warning(f"Unknown question type: {question_type}")
                return {"is_correct": False}

        except Exception as e:
            logger.error(f"Error grading answer: {e}")
            return {"is_correct": False}

    async def _grade_choice_answer(
        self,
        user_answer: str,
        correct_answer: str,
    ) -> Dict[str, Any]:
        """Grade multiple choice answer.

        Args:
            user_answer: User's answer (e.g., "A", "B", "C", "D")
            correct_answer: Correct answer

        Returns:
            Grading result
        """
        # Normalize answers (case insensitive, trim whitespace)
        user_normalized = user_answer.strip().upper()
        correct_normalized = correct_answer.strip().upper()

        is_correct = user_normalized == correct_normalized

        return {
            "is_correct": is_correct,
        }

    async def _grade_fill_blank_answer(
        self,
        user_answer: str,
        correct_answer: str,
    ) -> Dict[str, Any]:
        """Grade fill-in-the-blank answer using fuzzy matching.

        Args:
            user_answer: User's answer
            correct_answer: Correct answer

        Returns:
            Grading result
        """
        # Normalize
        user_normalized = user_answer.strip().lower()
        correct_normalized = correct_answer.strip().lower()

        # Direct match
        if user_normalized == correct_normalized:
            return {"is_correct": True}

        # Check if user answer contains key terms
        correct_keywords = correct_normalized.split()
        user_keywords = user_normalized.split()

        # Calculate keyword overlap
        matches = sum(1 for kw in correct_keywords if kw in user_normalized)
        match_ratio = matches / len(correct_keywords) if correct_keywords else 0

        # Consider correct if 70%+ keyword match
        is_correct = match_ratio >= 0.7

        return {
            "is_correct": is_correct,
        }

    async def _grade_short_answer(
        self,
        question: QuizQuestion,
        user_answer: str,
        correct_answer: str,
        quiz_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Grade short answer using LLM.

        Args:
            question: Quiz question
            user_answer: User's answer
            correct_answer: Correct answer
            quiz_id: Quiz ID

        Returns:
            Grading result with score and feedback
        """
        prompt = self._get_grading_prompt(
            question.question_text,
            user_answer,
            correct_answer,
        )

        try:
            response = await self.deepseek.generate_completion(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
            )

            # Parse response
            import json
            import re

            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                grading_data = json.loads(json_match.group(0))
            else:
                grading_data = json.loads(response)

            score = grading_data.get("score", 0.0)
            is_correct = score >= 0.6  # 60% threshold for correct

            result = {
                "is_correct": is_correct,
                "ai_score": score,
                "feedback": grading_data.get("feedback"),
            }

            # If incorrect, find relevant note snippets
            if not is_correct:
                snippets = await self.vector_search.find_relevant_snippets_for_wrong_answer(
                    question=question.question_text,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    note_id=str(quiz_id),  # Assuming note_id is available
                )
                result["note_snippets"] = snippets

            return result

        except Exception as e:
            logger.error(f"Failed to grade short answer with LLM: {e}")
            return {"is_correct": False}

    def _get_grading_prompt(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
    ) -> str:
        """Generate prompt for LLM grading.

        Args:
            question: Question text
            user_answer: User's answer
            correct_answer: Correct answer

        Returns:
            Formatted prompt
        """
        return f"""Grade the following short answer:

Question: {question}

User's Answer: {user_answer}

Correct Answer: {question}

Grading Criteria:
1. Score from 0.0 to 1.0 based on accuracy and completeness
2. Provide brief feedback explaining the score
3. Be fair and partial credit for partially correct answers

Output MUST be valid JSON only:
{{
  "score": 0.8,
  "feedback": "Brief explanation of the score"
}}

Grade the answer now:"""

    async def get_session_results(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[QuizSession]:
        """Get quiz session results.

        Args:
            session_id: Session ID
            user_id: User ID

        Returns:
            Quiz session with answers, None if not found
        """
        result = await self.db.execute(
            select(QuizSession).where(
                QuizSession.id == session_id,
                QuizSession.user_id == user_id,
            )
        )
        session = result.scalar_one_or_none()

        if session:
            await self.db.refresh(session, attribute_names=["answers"])

        return session

    async def close(self) -> None:
        """Close service connections."""
        await self.deepseek.close()
        await self.vector_search.close()
