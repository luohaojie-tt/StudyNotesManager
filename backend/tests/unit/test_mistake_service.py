"""
Unit tests for Mistake service and Ebbinghaus utility.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytest

from app.services.mistake_service import MistakeService
from app.schemas.mistake import MistakeCreate, MistakeUpdate, ReviewRecord
from app.utils.ebbinghaus import (
    calculate_next_review,
    calculate_mastery_level,
    get_review_status,
    minutes_until_review,
)


@pytest.mark.unit
class TestEbbinghausUtility:
    """Test Ebbinghaus forgetting curve utility."""

    def test_calculate_next_review_first_correct(self):
        """Test first correct review schedules 20 minutes."""
        next_review, consecutive = calculate_next_review(
            consecutive_correct=0,
            is_correct=True
        )

        assert consecutive == 1
        assert next_review > datetime.utcnow()
        time_diff = (next_review - datetime.utcnow()).total_seconds()
        assert 18 * 60 <= time_diff <= 22 * 60  # ~20 minutes

    def test_calculate_next_review_incorrect_resets(self):
        """Test incorrect review resets consecutive count."""
        next_review, consecutive = calculate_next_review(
            consecutive_correct=3,
            is_correct=False
        )

        assert consecutive == 0
        assert next_review > datetime.utcnow()
        time_diff = (next_review - datetime.utcnow()).total_seconds()
        assert 18 * 60 <= time_diff <= 22 * 60  # Back to 20 minutes

    def test_calculate_next_review_multiple_correct(self):
        """Test multiple correct reviews increase interval."""
        next_review, consecutive = calculate_next_review(
            consecutive_correct=3,
            is_correct=True
        )

        assert consecutive == 4
        # Should use 4th interval index (1440 minutes = 1 day)
        time_diff = (next_review - datetime.utcnow()).total_seconds()
        assert 1430 * 60 <= time_diff <= 1450 * 60

    def test_calculate_next_review_max_interval(self):
        """Test max interval is capped."""
        next_review, consecutive = calculate_next_review(
            consecutive_correct=10,
            is_correct=True
        )

        # Should cap at max interval (44640 minutes = 31 days)
        time_diff = (next_review - datetime.utcnow()).total_seconds()
        assert 44600 * 60 <= time_diff <= 44700 * 60

    def test_calculate_mastery_level_perfect(self):
        """Test perfect mastery level."""
        mastery = calculate_mastery_level(
            correct_count=5,
            incorrect_count=0,
            consecutive_correct=5
        )

        assert mastery == 100  # Max score

    def test_calculate_mastery_level_partial(self):
        """Test partial mastery level."""
        mastery = calculate_mastery_level(
            correct_count=3,
            incorrect_count=2,
            consecutive_correct=2
        )

        # Base: 3/5 = 60% of 50 = 30
        # Bonus: 2 consecutive = 20
        # Total: 50
        assert 45 <= mastery <= 55

    def test_calculate_mastery_level_no_reviews(self):
        """Test mastery level with no reviews."""
        mastery = calculate_mastery_level(
            correct_count=0,
            incorrect_count=0,
            consecutive_correct=0
        )

        assert mastery == 0

    def test_get_review_status_overdue(self):
        """Test review status for overdue review."""
        past_time = datetime.utcnow() - timedelta(hours=1)
        status = get_review_status(next_review_at=past_time)

        assert status == "overdue"

    def test_get_review_status_due(self):
        """Test review status for due review."""
        soon_time = datetime.utcnow() + timedelta(minutes=30)
        status = get_review_status(next_review_at=soon_time)

        assert status == "due"

    def test_get_review_status_scheduled(self):
        """Test review status for scheduled review."""
        future_time = datetime.utcnow() + timedelta(hours=2)
        status = get_review_status(next_review_at=future_time)

        assert status == "scheduled"

    def test_minutes_until_review_positive(self):
        """Test minutes until review for future time."""
        future_time = datetime.utcnow() + timedelta(minutes=30)
        minutes = minutes_until_review(next_review_at=future_time)

        assert 28 <= minutes <= 32

    def test_minutes_until_review_negative(self):
        """Test minutes until review for past time (overdue)."""
        past_time = datetime.utcnow() - timedelta(minutes=30)
        minutes = minutes_until_review(next_review_at=past_time)

        assert -32 <= minutes <= -28


@pytest.mark.unit
class TestMistakeService:
    """Test MistakeService methods."""

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
        db.delete = AsyncMock()  # Service awaits this
        return db

    @pytest.mark.asyncio
    async def test_create_mistake_success(self, mock_db):
        """Test successful mistake creation."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()
        mistake_data = MistakeCreate(
            question="What is 2+2?",
            correct_answer="4",
            user_answer="5",
            question_type="choice",
            subject="Math",
            knowledge_points=["Addition", "Basic Math"],
            difficulty=1,
            source="Quiz 1",
            tags=["easy", "arithmetic"]
        )

        mock_result = MagicMock()
        mock_db.execute.return_value = mock_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            mistake = await service.create_mistake(user_id, mistake_data)

            assert mistake.user_id == user_id
            assert mistake.question == mistake_data.question
            assert mistake.mastery_level == 0
            assert mistake.review_count == 0
            assert mistake.consecutive_correct == 0
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mistake_success(self, mock_db):
        """Test getting mistake by ID."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()
        mistake_id = uuid.uuid4()

        mock_mistake = MagicMock(spec=Mistake)
        mock_mistake.id = mistake_id
        mock_mistake.user_id = user_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mistake
        mock_db.execute.return_value = mock_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            mistake = await service.get_mistake(mistake_id, user_id)

            assert mistake is not None
            assert mistake.id == mistake_id

    @pytest.mark.asyncio
    async def test_get_mistake_not_found(self, mock_db):
        """Test getting non-existent mistake."""
        user_id = uuid.uuid4()
        mistake_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            mistake = await service.get_mistake(mistake_id, user_id)

            assert mistake is None

    @pytest.mark.asyncio
    async def test_get_mistakes_with_filters(self, mock_db):
        """Test getting mistakes with filters."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()

        # Mock mistakes list
        mock_mistakes = [MagicMock(spec=Mistake) for _ in range(3)]
        for m in mock_mistakes:
            m.user_id = user_id

        scalars_result = MagicMock()
        scalars_result.all.return_value = mock_mistakes

        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars_result
        result_mock.scalar.return_value = 10

        mock_db.execute.return_value = result_mock

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            mistakes, total = await service.get_mistakes(
                user_id=user_id,
                subject="Math",
                limit=10
            )

            assert len(mistakes) == 3
            assert total == 10

    @pytest.mark.asyncio
    async def test_delete_mistake_success(self, mock_db):
        """Test successful mistake deletion."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()
        mistake_id = uuid.uuid4()

        mock_mistake = MagicMock(spec=Mistake)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mistake
        mock_db.execute.return_value = mock_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            success = await service.delete_mistake(mistake_id, user_id)

            assert success is True
            mock_db.delete.assert_called_once_with(mock_mistake)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_mistake_not_found(self, mock_db):
        """Test deleting non-existent mistake."""
        user_id = uuid.uuid4()
        mistake_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            success = await service.delete_mistake(mistake_id, user_id)

            assert success is False

    @pytest.mark.asyncio
    async def test_review_mistake_correct(self, mock_db):
        """Test reviewing mistake with correct answer."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()
        mistake_id = uuid.uuid4()

        mock_mistake = MagicMock(spec=Mistake)
        mock_mistake.consecutive_correct = 0
        mock_mistake.correct_count = 2
        mock_mistake.review_count = 3

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mistake
        mock_db.execute.return_value = mock_result

        review_data = ReviewRecord(is_correct=True, time_spent=30)

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            result = await service.review_mistake(mistake_id, user_id, review_data)

            assert result is not None
            assert result.consecutive_correct == 1
            assert result.correct_count == 3
            assert result.review_count == 4
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_review_mistake_incorrect(self, mock_db):
        """Test reviewing mistake with incorrect answer."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()
        mistake_id = uuid.uuid4()

        mock_mistake = MagicMock(spec=Mistake)
        mock_mistake.consecutive_correct = 3
        mock_mistake.correct_count = 5
        mock_mistake.incorrect_count = 1

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mistake
        mock_db.execute.return_value = mock_result

        review_data = ReviewRecord(is_correct=False, time_spent=45)

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            result = await service.review_mistake(mistake_id, user_id, review_data)

            assert result is not None
            assert result.consecutive_correct == 0  # Reset on incorrect
            assert result.incorrect_count == 2
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_weak_points(self, mock_db):
        """Test weak points analysis."""
        from app.models.mistake import Mistake

        user_id = uuid.uuid4()

        # Create mock mistakes
        mock_mistakes = []
        for i in range(5):
            m = MagicMock(spec=Mistake)
            m.user_id = user_id
            m.is_archived = False
            m.subject = f"Subject {i % 2}"
            m.knowledge_points = [f"KP{i}"]
            m.review_count = i + 1
            m.correct_count = i
            m.mastery_level = i * 10
            m.created_at = datetime.utcnow()
            mock_mistakes.append(m)

        scalars_result = MagicMock()
        scalars_result.all.return_value = mock_mistakes
        mock_db.execute.return_value = scalars_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            weak_points = await service.analyze_weak_points(user_id, limit=3)

            assert len(weak_points) <= 3
            # Check that weak points have required fields
            for wp in weak_points:
                assert "knowledge_point" in wp
                assert "priority" in wp
                assert "error_rate" in wp

    @pytest.mark.asyncio
    async def test_get_due_review_count(self, mock_db):
        """Test getting due review count."""
        user_id = uuid.uuid4()
        due_count = 5

        mock_result = MagicMock()
        mock_result.scalar.return_value = due_count
        mock_db.execute.return_value = mock_result

        with patch.object(MistakeService, '__init__', lambda self, db: None):
            service = MistakeService(mock_db)
            service.db = mock_db

            count = await service.get_due_review_count(user_id)

            assert count == due_count
