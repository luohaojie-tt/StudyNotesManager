"""
Unit tests for quiz generation and grading services.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.quiz_generation_service import QuizGenerationService
from app.services.quiz_grading_service import QuizGradingService


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
        mock_quiz.status = "completed"
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
    async def test_get_quiz_questions(self, mock_db):
        """Test getting quiz questions."""
        quiz_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_question = MagicMock()
        mock_question.id = uuid.uuid4()
        mock_question.knowledge_point_id = uuid.uuid4()
        mock_question.question_text = "What is 2+2?"
        mock_question.question_type = "choice"
        mock_question.options = ["3", "4", "5"]
        mock_question.difficulty = "easy"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_question]
        mock_db.execute.return_value = mock_result

        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            questions = await service.get_quiz_questions(quiz_id, user_id)

            assert len(questions) == 1
            assert questions[0].question_text == "What is 2+2?"

    @pytest.mark.asyncio
    async def test_close_service(self, mock_db):
        """Test closing service connections."""
        with patch.object(QuizGenerationService, '__init__', lambda self, db: None):
            service = QuizGenerationService(mock_db)
            service.db = mock_db

            await service.close()
            # Should not raise any errors


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
        quiz_id = uuid.uuid4()
        user_id = uuid.uuid4()

        answers = [
            {
                "question_id": uuid.uuid4(),
                "user_answer": "4"
            }
        ]

        mock_session = MagicMock()
        mock_session.id = uuid.uuid4()
        mock_session.quiz_id = quiz_id
        mock_session.status = "completed"
        mock_session.total_questions = 1
        mock_session.correct_count = 1
        mock_session.score = 100.0
        mock_session.started_at = MagicMock()
        mock_session.completed_at = MagicMock()

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            # Mock vector search and grading
            with patch.object(service, '_grade_answer', return_value=(True, 1.0)):
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

    @pytest.mark.asyncio
    async def test_get_session_results(self, mock_db):
        """Test getting quiz session results."""
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_session = MagicMock()
        mock_session.id = session_id
        mock_session.quiz_id = uuid.uuid4()
        mock_session.status = "completed"
        mock_session.total_questions = 10
        mock_session.correct_count = 8
        mock_session.score = 80.0
        mock_session.started_at = MagicMock()
        mock_session.completed_at = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_session
        mock_db.execute.return_value = mock_result

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
        mock_db.execute.return_value = mock_result

        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db

            result = await service.get_session_results(session_id, user_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_initialize_service(self, mock_db):
        """Test initializing grading service."""
        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db
            service._initialize_vector_store = AsyncMock()

            await service.initialize()

            service._initialize_vector_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_service(self, mock_db):
        """Test closing service connections."""
        with patch.object(QuizGradingService, '__init__', lambda self, db: None):
            service = QuizGradingService(mock_db)
            service.db = mock_db
            service._close_vector_store = AsyncMock()

            await service.close()

            service._close_vector_store.assert_called_once()
