"""Quiz question quality validation service."""

import json
import re
import uuid
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.deepseek_service import DeepSeekService

settings = get_settings()


class QuizQualityValidator:
    """Service for validating quiz question quality."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize quality validator.

        Args:
            db: Database session
        """
        self.db = db
        self.deepseek = DeepSeekService()

    async def validate_question(
        self,
        question_data: Dict[str, Any],
        knowledge_point: str,
        expected_difficulty: str,
    ) -> Dict[str, Any]:
        """Validate a single question for quality.

        Args:
            question_data: Generated question data
            knowledge_point: Knowledge point text
            expected_difficulty: Expected difficulty level

        Returns:
            Validation result with is_valid, score, and feedback
        """
        try:
            # Check required fields
            if not self._has_required_fields(question_data):
                return {
                    "is_valid": False,
                    "score": 0.0,
                    "reason": "Missing required fields",
                }

            # Validate question text
            if not self._validate_question_text(question_data.get("question_text", "")):
                return {
                    "is_valid": False,
                    "score": 0.0,
                    "reason": "Question text is invalid or too short",
                }

            # Validate answer
            if not question_data.get("correct_answer"):
                return {
                    "is_valid": False,
                    "score": 0.0,
                    "reason": "Missing correct answer",
                }

            # Validate options for choice questions
            if question_data.get("question_type") == "choice":
                if not self._validate_choice_options(question_data.get("options", [])):
                    return {
                        "is_valid": False,
                        "score": 0.0,
                        "reason": "Invalid or insufficient options for choice question",
                    }

            # AI-based quality assessment
            quality_score = await self._assess_quality_with_ai(
                question_data=question_data,
                knowledge_point=knowledge_point,
                expected_difficulty=expected_difficulty,
            )

            is_valid = quality_score >= settings.QUIZ_QUALITY_THRESHOLD

            return {
                "is_valid": is_valid,
                "score": quality_score,
                "reason": "Quality validation passed" if is_valid else "Quality score below threshold",
            }

        except Exception as e:
            logger.error(f"Error validating question: {e}")
            return {
                "is_valid": False,
                "score": 0.0,
                "reason": f"Validation error: {str(e)}",
            }

    def _has_required_fields(self, question_data: Dict[str, Any]) -> bool:
        """Check if question has all required fields.

        Args:
            question_data: Question data

        Returns:
            True if all required fields present
        """
        required_fields = ["question_text", "correct_answer"]
        return all(field in question_data for field in required_fields)

    def _validate_question_text(self, question_text: str) -> bool:
        """Validate question text.

        Args:
            question_text: Question text

        Returns:
            True if valid
        """
        if not question_text or not isinstance(question_text, str):
            return False

        # Minimum length check
        if len(question_text.strip()) < 10:
            return False

        # Maximum length check
        if len(question_text) > 1000:
            return False

        # Check if it's actually a question (has question mark or question words)
        question_lower = question_text.lower()
        question_words = ["what", "how", "why", "when", "where", "which", "who", "explain", "describe"]

        has_question_mark = "?" in question_text
        has_question_word = any(word in question_lower for word in question_words)

        return has_question_mark or has_question_word

    def _validate_choice_options(self, options: List[str]) -> bool:
        """Validate choice question options.

        Args:
            options: List of options

        Returns:
            True if valid
        """
        if not options or not isinstance(options, list):
            return False

        # Need at least 3 options
        if len(options) < 3:
            return False

        # Check each option
        for option in options:
            if not option or not isinstance(option, str):
                return False
            if len(option.strip()) < 1:
                return False

        # Check for uniqueness
        unique_options = set(opt.strip().lower() for opt in options)
        if len(unique_options) < len(options):
            return False

        return True

    async def _assess_quality_with_ai(
        self,
        question_data: Dict[str, Any],
        knowledge_point: str,
        expected_difficulty: str,
    ) -> float:
        """Assess question quality using AI.

        Args:
            question_data: Question to assess
            knowledge_point: Related knowledge point
            expected_difficulty: Expected difficulty

        Returns:
            Quality score from 0.0 to 1.0
        """
        prompt = self._get_quality_prompt(question_data, knowledge_point, expected_difficulty)

        try:
            response = await self.deepseek.generate_completion(
                prompt=prompt,
                max_tokens=300,
                temperature=0.3,
            )

            # Parse JSON response
            json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if json_match:
                assessment = json.loads(json_match.group(0))
            else:
                assessment = json.loads(response)

            return assessment.get("quality_score", 0.5)

        except Exception as e:
            logger.error(f"Failed to assess quality with AI: {e}")
            # Return conservative score on error
            return 0.5

    def _get_quality_prompt(
        self,
        question_data: Dict[str, Any],
        knowledge_point: str,
        expected_difficulty: str,
    ) -> str:
        """Generate prompt for quality assessment.

        Args:
            question_data: Question data
            knowledge_point: Knowledge point text
            expected_difficulty: Expected difficulty

        Returns:
            Formatted prompt
        """
        question_text = question_data.get("question_text", "")
        correct_answer = question_data.get("correct_answer", "")
        question_type = question_data.get("question_type", "choice")

        return f"""Assess the quality of this quiz question:

Knowledge Point: {knowledge_point}
Question Type: {question_type}
Expected Difficulty: {expected_difficulty}

Question: {question_text}
Correct Answer: {correct_answer}

Assessment Criteria:
1. Relevance: Does the question test the knowledge point? (0-1)
2. Clarity: Is the question clear and unambiguous? (0-1)
3. Difficulty: Does it match the expected difficulty level? (0-1)
4. Answer Quality: Is the answer correct and complete? (0-1)

Calculate overall quality score (average of criteria, 0.0 to 1.0).

Output MUST be valid JSON only:
{{
  "quality_score": 0.85,
  "relevance": 0.9,
  "clarity": 0.8,
  "difficulty_match": 0.85,
  "answer_quality": 0.85
}}

Assess the question now:"""

    async def detect_duplicates(
        self,
        new_question: str,
        existing_questions: List[str],
    ) -> List[Dict[str, Any]]:
        """Detect duplicate or similar questions.

        Args:
            new_question: New question text
            existing_questions: List of existing question texts

        Returns:
            List of potential duplicates with similarity scores
        """
        if not existing_questions:
            return []

        duplicates = []

        for existing_q in existing_questions:
            similarity = await self._calculate_similarity(new_question, existing_q)

            if similarity >= settings.QUIZ_DUPLICATE_THRESHOLD:
                duplicates.append(
                    {
                        "question": existing_q,
                        "similarity": similarity,
                    }
                )

        return duplicates

    async def _calculate_similarity(self, question1: str, question2: str) -> float:
        """Calculate semantic similarity between two questions.

        Args:
            question1: First question
            question2: Second question

        Returns:
            Similarity score from 0.0 to 1.0
        """
        # Simple word overlap similarity (can be enhanced with embeddings)
        words1 = set(question1.lower().split())
        words2 = set(question2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        jaccard_similarity = len(intersection) / len(union) if union else 0.0

        return jaccard_similarity

    async def close(self) -> None:
        """Close service connections."""
        await self.deepseek.close()
