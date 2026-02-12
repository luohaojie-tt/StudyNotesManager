"""Quiz generation service."""

import uuid
from typing import Any, Dict, List

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import Quiz, QuizQuestion
from app.models.mindmap import KnowledgePoint
from app.services.deepseek_service import DeepSeekService
from app.services.quiz_quality_service import QuizQualityValidator
from app.core.config import get_settings

settings = get_settings()


class QuizGenerationService:
    """Service for generating quizzes from mindmaps."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize quiz generation service.

        Args:
            db: Database session
        """
        self.db = db
        self.deepseek = DeepSeekService()

    async def generate_quiz(
        self,
        mindmap_id: uuid.UUID,
        user_id: uuid.UUID,
        question_count: int = 10,
        question_types: List[str] = None,
        difficulty: str = "medium",
    ) -> Quiz:
        """Generate quiz from mindmap.

        Args:
            mindmap_id: Mindmap ID
            user_id: User ID
            question_count: Number of questions to generate
            question_types: List of question types ["choice", "fill_blank", "short_answer"]
            difficulty: Question difficulty (easy, medium, hard)

        Returns:
            Created quiz (in generating status)

        Raises:
            ValueError: If parameters are invalid
        """
        if question_types is None:
            question_types = ["choice", "fill_blank"]

        # Validate inputs
        if question_count > settings.QUIZ_MAX_COUNT:
            raise ValueError(f"Question count cannot exceed {settings.QUIZ_MAX_COUNT}")

        if difficulty not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be easy, medium, or hard")

        # Get knowledge points from mindmap
        knowledge_points = await self._get_knowledge_points(mindmap_id)

        if not knowledge_points:
            raise ValueError("No knowledge points found for mindmap")

        # Select knowledge points for questions
        selected_points = self._select_knowledge_points(
            knowledge_points,
            question_count,
        )

        # Create quiz record
        quiz = Quiz(
            id=uuid.uuid4(),
            mindmap_id=mindmap_id,
            user_id=user_id,
            question_count=question_count,
            difficulty=difficulty,
            question_types=question_types,
            status="generating",
        )

        self.db.add(quiz)
        await self.db.flush()

        # Generate questions for each knowledge point
        questions = await self._generate_questions(
            quiz.id,
            selected_points,
            question_types,
            difficulty,
        )

        # Update quiz status
        quiz.status = "ready"
        await self.db.commit()
        await self.db.refresh(quiz)

        logger.info(f"Generated quiz {quiz.id} with {len(questions)} questions")
        return quiz

    async def _get_knowledge_points(
        self,
        mindmap_id: uuid.UUID,
    ) -> List[KnowledgePoint]:
        """Get knowledge points for mindmap.

        Args:
            mindmap_id: Mindmap ID

        Returns:
            List of knowledge points
        """
        result = await self.db.execute(
            select(KnowledgePoint)
            .where(KnowledgePoint.mindmap_id == mindmap_id)
            .order_by(KnowledgePoint.level, KnowledgePoint.text)
        )
        return list(result.scalars().all())

    def _select_knowledge_points(
        self,
        knowledge_points: List[KnowledgePoint],
        count: int,
    ) -> List[KnowledgePoint]:
        """Select knowledge points for quiz generation.

        Args:
            knowledge_points: All available knowledge points
            count: Number to select

        Returns:
            Selected knowledge points
        """
        # Prioritize deeper levels (more specific concepts)
        sorted_points = sorted(
            knowledge_points,
            key=lambda kp: (kp.level, kp.text),
            reverse=True,
        )

        # Select from different levels for variety
        if len(sorted_points) <= count:
            return sorted_points

        # Stratified sampling by level with remainder handling
        selected = []
        levels = set(kp.level for kp in sorted_points)
        num_levels = len(levels)

        # Calculate base count per level and remainder
        base_count = count // num_levels
        remainder = count % num_levels

        # Select from each level (sorted by level descending)
        for idx, level in enumerate(sorted(levels, reverse=True)):
            level_points = [kp for kp in sorted_points if kp.level == level]
            # First 'remainder' levels get one extra
            level_count = base_count + (1 if idx < remainder else 0)

            # Don't select more than available at this level
            level_count = min(level_count, len(level_points))
            selected.extend(level_points[:level_count])

        # Fallback: if we still don't have enough, add from highest levels
        if len(selected) < count and len(selected) < len(sorted_points):
            remaining_needed = count - len(selected)
            already_selected_ids = set(kp.id for kp in selected)
            for kp in sorted_points:
                if len(selected) >= count:
                    break
                if kp.id not in already_selected_ids:
                    selected.append(kp)

        return selected[:count]

    async def _generate_questions(
        self,
        quiz_id: uuid.UUID,
        knowledge_points: List[KnowledgePoint],
        question_types: List[str],
        difficulty: str,
    ) -> List[QuizQuestion]:
        """Generate questions for knowledge points with quality validation.

        Args:
            quiz_id: Quiz ID
            knowledge_points: Knowledge points to generate questions for
            question_types: Allowed question types
            difficulty: Question difficulty

        Returns:
            List of generated questions
        """
        questions = []
        quality_validator = QuizQualityValidator(self.db)

        for idx, kp in enumerate(knowledge_points):
            # Select question type for this knowledge point
            q_type = question_types[idx % len(question_types)]

            # Retry logic for quality validation
            max_retries = settings.QUIZ_MAX_RETRIES
            valid_question = None

            for attempt in range(max_retries):
                try:
                    # Generate question using DeepSeek
                    question_data = await self._generate_single_question(
                        knowledge_point=kp.text,
                        question_type=q_type,
                        difficulty=difficulty,
                    )

                    # Check for duplicates with existing questions
                    existing_questions = [q.question_text for q in questions]
                    duplicates = await quality_validator.detect_duplicates(
                        question_data["question_text"],
                        existing_questions,
                    )

                    if duplicates:
                        logger.warning(
                            f"Duplicate detected for knowledge point {kp.id}, retrying... (attempt {attempt + 1}/{max_retries})"
                        )
                        continue

                    # Validate quality
                    validation_result = await quality_validator.validate_question(
                        question_data=question_data,
                        knowledge_point=kp.text,
                        expected_difficulty=difficulty,
                    )

                    if not validation_result["is_valid"]:
                        logger.warning(
                            f"Question validation failed for knowledge point {kp.id}: {validation_result['reason']}. "
                            f"Retrying... (attempt {attempt + 1}/{max_retries})"
                        )
                        continue

                    # Question is valid
                    valid_question = question_data
                    break

                except Exception as e:
                    logger.error(
                        f"Error generating question for knowledge point {kp.id} (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    if attempt == max_retries - 1:
                        # Last attempt failed, skip this knowledge point
                        logger.error(f"Failed to generate valid question for knowledge point {kp.id} after {max_retries} attempts")
                        continue

            # Create question record if valid
            if valid_question:
                question = QuizQuestion(
                    id=uuid.uuid4(),
                    quiz_id=quiz_id,
                    knowledge_point_id=kp.id,
                    question_text=valid_question["question_text"],
                    question_type=q_type,
                    options=valid_question.get("options"),
                    correct_answer=valid_question["correct_answer"],
                    explanation=valid_question.get("explanation"),
                    difficulty=difficulty,
                    order=idx + 1,
                )

                self.db.add(question)
                questions.append(question)

        await quality_validator.close()
        return questions

    async def _generate_single_question(
        self,
        knowledge_point: str,
        question_type: str,
        difficulty: str,
    ) -> Dict[str, Any]:
        """Generate a single question.

        Args:
            knowledge_point: Knowledge point text
            question_type: Type of question
            difficulty: Difficulty level

        Returns:
            Question data

        Raises:
            ValueError: If generation fails
        """
        prompt = self._get_question_prompt(knowledge_point, question_type, difficulty)

        try:
            response = await self.deepseek.generate_completion(
                prompt=prompt,
                max_tokens=500,
                temperature=0.5,
            )

            # Parse JSON response
            import json
            import re

            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                question_data = json.loads(json_match.group(0))
            else:
                question_data = json.loads(response)

            # Validate required fields
            if "question_text" not in question_data or "correct_answer" not in question_data:
                raise ValueError("Missing required fields in question")

            # Ensure options for choice questions
            if question_type == "choice" and "options" not in question_data:
                raise ValueError("Choice questions must have options")

            return question_data

        except Exception as e:
            logger.error(f"Failed to parse question response: {e}")
            raise ValueError(f"Invalid question format: {e}")

    def _get_question_prompt(
        self,
        knowledge_point: str,
        question_type: str,
        difficulty: str,
    ) -> str:
        """Generate prompt for question creation.

        Args:
            knowledge_point: Knowledge point text
            question_type: Type of question
            difficulty: Difficulty level

        Returns:
            Formatted prompt
        """
        type_instructions = {
            "choice": "Create a multiple choice question with 4 options (A, B, C, D).",
            "fill_blank": "Create a fill-in-the-blank question with a clear answer.",
            "short_answer": "Create a short answer question requiring 2-3 sentences.",
        }

        return f"""Generate a {difficulty} {question_type} question for this knowledge point: {knowledge_point}

Requirements:
1. {type_instructions.get(question_type, "")}
2. Question should test understanding of the concept
3. Output MUST be valid JSON only

JSON Format:
{{
  "question_text": "Your question here",
  "correct_answer": "The correct answer",
  "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
  "explanation": "Brief explanation of the answer"
}}

Generate the question now:"""

    async def get_quiz_questions(
        self,
        quiz_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[QuizQuestion]:
        """Get questions for a quiz.

        Args:
            quiz_id: Quiz ID
            user_id: User ID

        Returns:
            List of questions

        Raises:
            ValueError: If quiz not found or unauthorized
        """
        # Verify authorization
        result = await self.db.execute(
            select(Quiz).where(
                Quiz.id == quiz_id,
                Quiz.user_id == user_id,
            )
        )
        quiz = result.scalar_one_or_none()

        if not quiz:
            raise ValueError("Quiz not found or unauthorized")

        # Get questions
        result = await self.db.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.order)
        )
        return list(result.scalars().all())

    async def close(self) -> None:
        """Close service connections."""
        await self.deepseek.close()
