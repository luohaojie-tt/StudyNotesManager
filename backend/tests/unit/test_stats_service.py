"""
Unit tests for clean Stats service.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytest

from app.services.stats_service import StatsService


@pytest.mark.unit
class TestStatsOverview:
    """Test overview statistics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_overview_basic_counts(self, mock_db):
        """Test getting overview with basic counts."""
        user_id = uuid.uuid4()

        # Mock count results
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10  # Total notes

        mock_db.execute.return_value = mock_result

        with patch.object(StatsService, '__init__', lambda self, db: None):
            service = StatsService(mock_db)
            service.db = mock_db

            overview = await service.get_overview(user_id)

            assert overview["total_notes"] == 10

    @pytest.mark.asyncio
    async def test_get_overview_with_study_time(self, mock_db):
        """Test getting overview with study time."""
        user_id = uuid.uuid4()

        # Mock to return different values for different queries
        call_count = 0

        async def mock_execute(query):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return MagicMock(scalar=MagicMock(return_value=10))
            elif call_count == 2:
                return MagicMock(scalar=MagicMock(return_value=5))
            elif call_count == 3:
                return MagicMock(scalar=MagicMock(return_value=3))
            elif call_count == 4:
                return MagicMock(scalar=MagicMock(return_value=3600))  # 1 hour in seconds
            else:
                return MagicMock(scalar=MagicMock(return_value=0))

        mock_db.execute.side_effect = mock_execute

        with patch.object(StatsService, '__init__', lambda self, db: None):
            service = StatsService(mock_db)
            service.db = mock_db

            overview = await service.get_overview(user_id)

            assert overview["total_notes"] == 10
            assert overview["total_quizzes"] == 5
            assert overview["total_mistakes"] == 3
            assert overview["total_study_time_minutes"] == 60


@pytest.mark.unit
class TestStatsQuizzes:
    """Test quiz statistics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_quiz_stats_basic(self, mock_db):
        """Test getting quiz performance stats."""
        user_id = uuid.uuid4()

        # Mock quiz session aggregation
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.total_quizzes = 1
        mock_row.avg_score = 85.0
        mock_row.total_questions = 100
        mock_row.total_correct = 85
        mock_result.one.return_value = mock_row

        mock_db.execute.return_value = mock_result

        with patch.object(StatsService, '__init__', lambda self, db: None):
            service = StatsService(mock_db)
            service.db = mock_db

            stats = await service.get_quiz_stats(user_id)

            assert stats["average_score"] == 85.0
            assert stats["total_quizzes"] == 1
            assert stats["completion_rate"] == 0.85


@pytest.mark.unit
class TestStatsMistakes:
    """Test mistake statistics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_mistake_stats_basic(self, mock_db):
        """Test getting mistake statistics."""
        user_id = uuid.uuid4()

        # Mock mistake count
        mock_result = MagicMock()
        mock_result.scalar.return_value = 15

        mock_db.execute.return_value = mock_result

        with patch.object(StatsService, '__init__', lambda self, db: None):
            service = StatsService(mock_db)
            service.db = mock_db

            stats = await service.get_mistake_stats(user_id)

            assert stats["total_mistakes"] == 15
            assert "mastery_distribution" in stats
            assert "weak_knowledge_points" in stats

    @pytest.mark.asyncio
    async def test_get_mistake_stats_with_weak_points(self, mock_db):
        """Test getting weak knowledge points."""
        user_id = uuid.uuid4()

        # Mock aggregation query
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_rows = [
            MagicMock(subject="Math", count=5, mastery_level=30),
            MagicMock(subject="Physics", count=3, mastery_level=20),
        ]
        mock_scalars.all.return_value = mock_rows
        mock_result.scalars.return_value = mock_scalars

        mock_db.execute.return_value = mock_result

        with patch.object(StatsService, '__init__', lambda self, db: None):
            service = StatsService(mock_db)
            service.db = mock_db

            stats = await service.get_mistake_stats(user_id)

            assert len(stats["weak_knowledge_points"]) == 2
            assert stats["weak_knowledge_points"][0]["subject"] == "Math"
