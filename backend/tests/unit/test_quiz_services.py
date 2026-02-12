"""
Unit tests for quiz generation and grading services.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.quiz_generation_service import QuizGenerationService
from app.services.quiz_grading_service import QuizGradingService
from app.services.quiz_quality_service import QuizQualityValidator
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data



@pytest.mark.unit
class TestQuizGenerationService:
    """Test QuizGenerationService methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_generate_quiz_success(self, mock_db):
        """Test successful quiz generation."""
        # Arrange
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_quiz = MagicMock()
        mock_quiz.id = uuid.uuid4()
        mock_quiz.status = "ready"
        mock_quiz.question_count = 10

        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            # Mock the internal generation method
            with patch.object(service, '_generate_questions', return_value=[]):
                service.db.add = MagicMock()
                service.db.flush = AsyncMock()
                service.db.commit = AsyncMock()
                service.db.refresh = AsyncMock()
                service.db.execute = AsyncMock()

                # Mock _get_knowledge_points
                mock_kp = MagicMock()
                mock_kp.id = uuid.uuid4()
                mock_kp.text = "Test knowledge point"
                mock_kp.level = 1

                mock_result = MagicMock()
                mock_result.scalars.return_value.all.return_value = [mock_kp]
                service.db.execute.return_value = mock_result

                # Act
                result = await service.generate_quiz(
                    mindmap_id=mindmap_id,
                    user_id=user_id,
                    question_count=10,
                    question_types=["choice"],
                    difficulty="medium"
                )

                # Assert
                assert result is not None
                service.db.add.assert_called()

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_question_count(self, mock_db):
        """Test quiz generation with invalid question count."""
        from app.core.config import get_settings

        settings = get_settings()

        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            # Act & Assert
            with pytest.raises(ValueError, match="Question count cannot exceed"):
                await service.generate_quiz(
                    mindmap_id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    question_count=settings.QUIZ_MAX_COUNT + 1,
                    question_types=["choice"],
                    difficulty="medium"
                )

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_difficulty(self, mock_db):
        """Test quiz generation with invalid difficulty."""
        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            # Act & Assert
            with pytest.raises(ValueError, match="Difficulty must be"):
                await service.generate_quiz(
                    mindmap_id=uuid.uuid4(),
                    user_id=uuid.uuid4(),
                    question_count=10,
                    question_types=["choice"],
                    difficulty="invalid"
                )

    @pytest.mark.asyncio
    async def test_get_quiz_questions_success(self, mock_db):
        """Test getting quiz questions successfully."""
        quiz_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_quiz = MagicMock()
        mock_quiz.id = quiz_id
        mock_quiz.user_id = user_id

        mock_question = MagicMock()
        mock_question.id = uuid.uuid4()
        mock_question.knowledge_point_id = uuid.uuid4()
        mock_question.question_text = "What is 2+2?"
        mock_question.question_type = "choice"
        mock_question.options = ["3", "4", "5"]
        mock_question.difficulty = "easy"
        mock_question.order = 1

        # Mock quiz query
        quiz_result = MagicMock()
        quiz_result.scalar_one_or_none.return_value = mock_quiz

        # Mock questions query
        questions_result = MagicMock()
        questions_result.scalars.return_value.all.return_value = [mock_question]

        mock_db.execute.return_value = MagicMock()

        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            # Setup execute to return different results
            execute_results = [quiz_result, questions_result]
            mock_db.execute = AsyncMock(side_effect=execute_results)

            questions = await service.get_quiz_questions(quiz_id, user_id)

            assert len(questions) == 1
            assert questions[0].question_text == "What is 2+2?"

    @pytest.mark.asyncio
    async def test_get_quiz_questions_unauthorized(self, mock_db):
        """Test getting quiz questions without authorization."""
        quiz_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock quiz not found
        quiz_result = MagicMock()
        quiz_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=quiz_result)

        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            # Act & Assert
            with pytest.raises(ValueError, match="Quiz not found or unauthorized"):
                await service.get_quiz_questions(quiz_id, user_id)

    @pytest.mark.asyncio
    async def test_select_knowledge_points(self, mock_db):
        """Test knowledge point selection strategy."""
        from app.models.mindmap import KnowledgePoint

        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)

            # Create mock knowledge points
            kps = []
            for i in range(10):
                kp = MagicMock(spec=KnowledgePoint)
                kp.id = uuid.uuid4()
                kp.text = f"Knowledge Point {i}"
                kp.level = i % 3
                kps.append(kp)

            # Test selecting 5 points
            selected = service._select_knowledge_points(kps, 5)

            assert len(selected) == 5
            # Should select from different levels
            levels = set(kp.level for kp in selected)
            assert len(levels) > 1


@pytest.mark.unit
class TestQuizGradingService:
    """Test QuizGradingService methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_submit_answers_success(self, mock_db):
        """Test submitting quiz answers for grading."""
        from app.models.quiz import Quiz, QuizQuestion, QuizSession

        quiz_id = uuid.uuid4()
        user_id = uuid.uuid4()

        # Mock quiz
        mock_quiz = MagicMock(spec=Quiz)
        mock_quiz.id = quiz_id

        # Mock questions
        mock_question = MagicMock(spec=QuizQuestion)
        mock_question.id = uuid.uuid4()
        mock_question.question_type = "choice"
        mock_question.correct_answer = "4"

        answers = [
            {
                "question_id": str(mock_question.id),
                "user_answer": "4"
            }
        ]

        mock_session = MagicMock(spec=QuizSession)
        mock_session.id = uuid.uuid4()
        mock_session.quiz_id = quiz_id
        mock_session.status = "completed"
        mock_session.total_questions = 1
        mock_session.correct_count = 1
        mock_session.score = 1.0
        mock_session.started_at = MagicMock()
        mock_session.completed_at = MagicMock()

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            # Mock methods
            service._get_quiz = AsyncMock(return_value=mock_quiz)
            service._get_quiz_questions = AsyncMock(return_value=[mock_question])
            service._grade_answer = AsyncMock(
                return_value={"is_correct": True}
            )

            service.db.add = MagicMock()
            service.db.flush = AsyncMock()
            service.db.commit = AsyncMock()
            service.db.refresh = AsyncMock()

            # Act
            result = await service.submit_answers(
                quiz_id=quiz_id,
                user_id=user_id,
                answers=answers
            )

            # Assert
            assert result is not None
            assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_submit_answers_quiz_not_found(self, mock_db):
        """Test submitting answers for non-existent quiz."""
        quiz_id = uuid.uuid4()
        user_id = uuid.uuid4()
        answers = []

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db
            service._get_quiz = AsyncMock(return_value=None)

            # Act & Assert
            with pytest.raises(ValueError, match="Quiz not found or unauthorized"):
                await service.submit_answers(
                    quiz_id=quiz_id,
                    user_id=user_id,
                    answers=answers
                )

    @pytest.mark.asyncio
    async def test_grade_choice_answer_correct(self, mock_db):
        """Test grading multiple choice answer - correct."""
        from app.models.quiz import QuizQuestion

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            mock_question = MagicMock(spec=QuizQuestion)
            mock_question.question_type = "choice"
            mock_question.correct_answer = "A"

            result = await service._grade_choice_answer(
                user_answer="a",  # Case insensitive
                correct_answer="A"
            )

            assert result["is_correct"] is True

    @pytest.mark.asyncio
    async def test_grade_choice_answer_incorrect(self, mock_db):
        """Test grading multiple choice answer - incorrect."""
        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            result = await service._grade_choice_answer(
                user_answer="B",
                correct_answer="A"
            )

            assert result["is_correct"] is False

    @pytest.mark.asyncio
    async def test_grade_fill_blank_exact_match(self, mock_db):
        """Test grading fill-in-the-blank - exact match."""
        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            result = await service._grade_fill_blank_answer(
                user_answer="  Paris  ",  # Extra spaces
                correct_answer="paris"
            )

            assert result["is_correct"] is True

    @pytest.mark.asyncio
    async def test_grade_fill_blank_partial_match(self, mock_db):
        """Test grading fill-in-blank - partial keyword match."""
        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            result = await service._grade_fill_blank_answer(
                user_answer="Paris is the capital of France",
                correct_answer="Paris is the capital city"
            )

            # Should have high keyword overlap
            assert result["is_correct"] is True

    @pytest.mark.asyncio
    async def test_get_session_results(self, mock_db):
        """Test getting quiz session results."""
        from app.models.quiz import QuizSession

        session_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_session = MagicMock(spec=QuizSession)
        mock_session.id = session_id
        mock_session.quiz_id = uuid.uuid4()
        mock_session.status = "completed"
        mock_session.total_questions = 10
        mock_session.correct_count = 8
        mock_session.score = 80.0
        mock_session.started_at = MagicMock()
        mock_session.completed_at = MagicMock()
        mock_session.answers = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.refresh = AsyncMock()

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            result = await service.get_session_results(session_id, user_id)

            assert result is not None
            assert result.id == session_id

    @pytest.mark.asyncio
    async def test_get_session_results_not_found(self, mock_db):
        """Test getting non-existent session results."""
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            result = await service.get_session_results(session_id, user_id)

            assert result is None


@pytest.mark.unit
class TestQuizQualityValidator:
    """Test QuizQualityValidator methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_validate_question_success(self, mock_db):
        """Test validating a good quality question."""
        question_data = {
            "question_text": "What is the capital of France?",
            "question_type": "choice",
            "correct_answer": "Paris",
            "options": ["A. London", "B. Paris", "C. Berlin", "D. Madrid"]
        }

        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            # Mock AI assessment
            validator._assess_quality_with_ai = AsyncMock(return_value=0.85)

            result = await validator.validate_question(
                question_data=question_data,
                knowledge_point="European capitals",
                expected_difficulty="easy"
            )

            assert result["is_valid"] is True
            assert result["score"] >= 0.7

    @pytest.mark.asyncio
    async def test_validate_question_missing_fields(self, mock_db):
        """Test validating question with missing fields."""
        question_data = {
            "question_text": "What is the capital?",
            # Missing correct_answer
        }

        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            result = await validator.validate_question(
                question_data=question_data,
                knowledge_point="Geography",
                expected_difficulty="easy"
            )

            assert result["is_valid"] is False
            assert "Missing required fields" in result["reason"]

    @pytest.mark.asyncio
    async def test_validate_question_invalid_text(self, mock_db):
        """Test validating question with invalid text."""
        question_data = {
            "question_text": "Hi",  # Too short
            "correct_answer": "Hello"
        }

        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            result = await validator.validate_question(
                question_data=question_data,
                knowledge_point="Greetings",
                expected_difficulty="easy"
            )

            assert result["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_choice_invalid_options(self, mock_db):
        """Test validating choice question with insufficient options."""
        question_data = {
            "question_text": "What is 2+2?",
            "question_type": "choice",
            "correct_answer": "4",
            "options": ["3", "4"]  # Only 2 options
        }

        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            result = await validator.validate_question(
                question_data=question_data,
                knowledge_point="Math",
                expected_difficulty="easy"
            )

            assert result["is_valid"] is False
            assert "options" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_detect_duplicates_with_similar(self, mock_db):
        """Test duplicate detection with similar questions."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            existing_questions = [
                "What is the capital of France?",
                "What is 2+2?",
                "Who wrote Romeo and Juliet?"
            ]

            validator._calculate_similarity = AsyncMock(side_effect=[0.95, 0.1, 0.2])

            duplicates = await validator.detect_duplicates(
                new_question="What is France's capital?",
                existing_questions=existing_questions
            )

            # Should find at least one duplicate (high similarity)
            assert len(duplicates) >= 1
            assert duplicates[0]["similarity"] >= 0.85

    @pytest.mark.asyncio
    async def test_detect_duplicates_no_duplicates(self, mock_db):
        """Test duplicate detection with no similar questions."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            existing_questions = [
                "What is the capital of France?",
                "What is 2+2?",
            ]

            validator._calculate_similarity = AsyncMock(return_value=0.3)

            duplicates = await validator.detect_duplicates(
                new_question="Who wrote Hamlet?",
                existing_questions=existing_questions
            )

            assert len(duplicates) == 0

    @pytest.mark.asyncio
    async def test_calculate_similarity_high_overlap(self, mock_db):
        """Test similarity calculation with high word overlap."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            similarity = await validator._calculate_similarity(
                question1="What is the capital of France?",
                question2="What is France's capital city?"
            )

            # Should have high similarity due to shared words
            assert similarity > 0.3

    def test_has_required_fields_all_present(self, mock_db):
        """Test _has_required_fields with all fields present."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            question_data = {
                "question_text": "What is 2+2?",
                "correct_answer": "4",
                "options": ["3", "4", "5"]
            }

            assert validator._has_required_fields(question_data) is True

    def test_has_required_fields_missing(self, mock_db):
        """Test _has_required_fields with missing fields."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            question_data = {
                "question_text": "What is 2+2?",
                # Missing correct_answer
            }

            assert validator._has_required_fields(question_data) is False

    def test_validate_question_text_valid(self, mock_db):
        """Test _validate_question_text with valid text."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            assert validator._validate_question_text("What is the capital of France?") is True
            assert validator._validate_question_text("Explain the process of photosynthesis.") is True

    def test_validate_question_text_invalid(self, mock_db):
        """Test _validate_question_text with invalid text."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            assert validator._validate_question_text("Hi") is False  # Too short
            assert validator._validate_question_text("") is False  # Empty

    def test_validate_choice_options_valid(self, mock_db):
        """Test _validate_choice_options with valid options."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            options = ["A. Paris", "B. London", "C. Berlin", "D. Madrid"]
            assert validator._validate_choice_options(options) is True

    def test_validate_choice_options_invalid(self, mock_db):
        """Test _validate_choice_options with invalid options."""
        with patch.object(QuizQualityValidator, '__init__', lambda self, db: None):
            validator = QuizQualityValidator(mock_db)
            validator.db = mock_db

            # Too few options
            assert validator._validate_choice_options(["A", "B"]) is False
            # Empty options
            assert validator._validate_choice_options([]) is False
            # Duplicate options
            assert validator._validate_choice_options(["Paris", "Paris", "London"]) is False
