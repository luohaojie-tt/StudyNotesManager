"""
Unit tests for Analytics service.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import pytest

from app.services.analytics_service import AnalyticsService


@pytest.mark.unit
class TestAnalyticsOverview:
    """Test analytics overview functionality."""

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
        notes_result = MagicMock()
        notes_result.scalar.return_value = 10

        quizzes_result = MagicMock()
        quizzes_result.scalar.return_value = 5

        mistakes_result = MagicMock()
        mistakes_result.scalar.return_value = 3

        accuracy_result = MagicMock()
        accuracy_result.scalar.return_value = 0.75

        study_time_result = MagicMock()
        study_time_result.scalar.return_value = 3600  # 1 hour

        # Setup execute to return different results
        mock_db.execute.side_effect = [
            notes_result,
            quizzes_result,
            mistakes_result,
            accuracy_result,
            study_time_result,
            MagicMock(),  # For recent activity
        ]

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            # Mock study streak calculation
            service._calculate_study_streak = AsyncMock(return_value=5)

            overview = await service.get_overview(user_id)

            assert overview["stats"]["total_notes"] == 10
            assert overview["stats"]["total_quizzes"] == 5
            assert overview["stats"]["total_mistakes"] == 3
            assert overview["stats"]["accuracy_rate"] == 0.75
            assert overview["stats"]["study_streak"] == 5
            assert overview["stats"]["total_study_time_minutes"] == 60

    @pytest.mark.asyncio
    async def test_get_overview_zero_data(self, mock_db):
        """Test overview when user has no data."""
        user_id = uuid.uuid4()

        # Mock zero results
        for scalar_val in [0, None, 0, None]:
            result = MagicMock()
            result.scalar.return_value = scalar_val
            mock_db.execute.return_value = result

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            service._calculate_study_streak = AsyncMock(return_value=0)

            overview = await service.get_overview(user_id)

            assert overview["stats"]["total_notes"] == 0
            assert overview["stats"]["accuracy_rate"] == 0.0
            assert overview["stats"]["study_streak"] == 0


@pytest.mark.unit
class TestAnalyticsPerformance:
    """Test performance analytics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_performance_basic(self, mock_db):
        """Test getting performance trends."""
        user_id = uuid.uuid4()

        # Mock performance trends
        trend_result = MagicMock()
        trend_result.scalars.return_value.all.return_value = [
            {
                "date": "2026-01-01",
                "score": 0.8,
                "quiz_count": 5,
                "questions_answered": 20,
            },
            {
                "date": "2026-01-02",
                "score": 0.85,
                "quiz_count": 3,
                "questions_answered": 15,
            },
        ]

        mock_db.execute.return_value = trend_result

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            service._get_performance_trends = AsyncMock(return_value=[])
            service._analyze_knowledge_areas = AsyncMock(return_value=([], []))

            performance = await service.get_performance(user_id)

            assert "daily_trends" in performance
            assert "weekly_trends" in performance
            assert "strong_areas" in performance
            assert "weak_areas" in performance

    @pytest.mark.asyncio
    async def test_analyze_knowledge_areas(self, mock_db):
        """Test knowledge area analysis."""
        user_id = uuid.uuid4()

        # Mock knowledge area data
        area_result = MagicMock()
        area_result.__iter__ = lambda self: iter([
            {
                "area": "easy",
                "total_questions": 10,
                "correct_questions": 9,
                "accuracy_rate": 0.9,
                "avg_mastery_level": 90,
            },
            {
                "area": "medium",
                "total_questions": 10,
                "correct_questions": 5,
                "accuracy_rate": 0.5,
                "avg_mastery_level": 50,
            },
            {
                "area": "hard",
                "total_questions": 10,
                "correct_questions": 2,
                "accuracy_rate": 0.2,
                "avg_mastery_level": 20,
            },
        ])

        mock_db.execute.return_value = area_result

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            strong, weak = await service._analyze_knowledge_areas(user_id)

            assert len(strong) == 1  # Top 50%
            assert len(weak) == 2  # Bottom 50%
            assert strong[0]["area"] == "easy"
            assert weak[-1]["area"] == "hard"


@pytest.mark.unit
class TestAnalyticsMistakes:
    """Test mistake analytics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_mistakes_analysis(self, mock_db):
        """Test getting mistake analysis."""
        user_id = uuid.uuid4()

        # Mock mistake data
        total_result = MagicMock()
        total_result.scalar.return_value = 15

        # Mock common topics
        topics_result = MagicMock()
        topics_result.__iter__ = lambda self: iter([
            MagicMock(topic="Math addition", count=5),
            MagicMock(topic="French grammar", count=3),
        ])

        # Mock categories
        category_result = MagicMock()
        category_result.__iter__ = lambda self: iter([
            MagicMock(
                category_id=uuid.uuid4(),
                category_name="Math",
                count=10
            ),
            MagicMock(
                category_id=uuid.uuid4(),
                category_name="Language",
                count=5
            ),
        ])

        # Mock recommendations
        rec_result = MagicMock()
        mock_mistakes = [MagicMock(id=uuid.uuid4()) for _ in range(3)]
        rec_result.scalars.return_value.all.return_value = mock_mistakes

        mock_db.execute.side_effect = [
            total_result,
            topics_result,
            category_result,
            rec_result,
        ]

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            analysis = await service.get_mistakes_analysis(user_id)

            assert analysis["total_mistakes"] == 15
            assert len(analysis["common_topics"]) == 2
            assert len(analysis["by_category"]) == 2
            assert len(analysis["review_recommendations"]) == 3


@pytest.mark.unit
class TestAnalyticsStudyTime:
    """Test study time analytics functionality."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_study_time_basic(self, mock_db):
        """Test getting study time analytics."""
        user_id = uuid.uuid4()

        # Mock study time data
        total_result = MagicMock()
        total_row = MagicMock()
        total_row.total_seconds = 7200  # 2 hours
        total_row.total_sessions = 5
        total_result.one.return_value = total_row

        # Mock category data
        category_result = MagicMock()
        category_result.__iter__ = lambda self: iter([
            MagicMock(
                category_id=uuid.uuid4(),
                category_name="Math",
                total_seconds=3600,
                session_count=3
            ),
        ])

        # Mock daily patterns
        patterns_result = MagicMock()
        patterns_result.__iter__ = lambda self: iter([
            MagicMock(
                date="2026-01-01",
                total_minutes=60,
                session_count=2,
                notes_created=5,
                questions_answered=1,
            ),
        ])

        mock_db.execute.side_effect = [
            total_result,
            category_result,
            patterns_result,
        ]

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            service._get_daily_study_patterns = AsyncMock(return_value=[])

            study_time = await service.get_study_time(user_id)

            assert study_time["total_study_time_minutes"] == 120  # 7200/60
            assert study_time["total_sessions"] == 5
            assert study_time["avg_session_duration_minutes"] == 24.0
            assert len(study_time["by_category"]) == 1

    @pytest.mark.asyncio
    async def test_calculate_study_streak(self, mock_db):
        """Test study streak calculation."""
        user_id = uuid.uuid4()

        # Mock study dates (consecutive days)
        dates_result = MagicMock()
        today = datetime.utcnow().date()
        dates_result.__iter__ = lambda self: iter([
            MagicMock(**{"study_date": today - timedelta(days=i)}),
            MagicMock(**{"study_date": today - timedelta(days=i)}),
            MagicMock(**{"study_date": today - timedelta(days=i)}),
        ])

        mock_db.execute.return_value = dates_result

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            streak = await service._calculate_study_streak(user_id)

            assert streak == 3


@pytest.mark.unit
class TestAnalyticsPerformanceTrends:
    """Test performance trend calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_daily_trends(self, mock_db):
        """Test getting daily performance trends."""
        user_id = uuid.uuid4()

        trend_result = MagicMock()
        trend_result.__iter__ = lambda self: iter([
            MagicMock(
                date="2026-01-01",
                score=0.8,
                quiz_count=5,
                questions_answered=20,
            ),
            MagicMock(
                date="2026-01-02",
                score=0.85,
                quiz_count=3,
                questions_answered=15,
            ),
        ])

        mock_db.execute.return_value = trend_result

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            trends = await service._get_performance_trends(
                user_id,
                days=30,
                group_by="day"
            )

            assert len(trends) == 2
            assert trends[0]["date"] == "2026-01-01"

    @pytest.mark.asyncio
    async def test_get_weekly_trends(self, mock_db):
        """Test getting weekly performance trends."""
        user_id = uuid.uuid4()

        mock_db.execute.return_value.__iter__ = lambda self: iter([
            MagicMock(date="2026-W01", score=0.75, quiz_count=10),
        ])

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            trends = await service._get_performance_trends(
                user_id,
                weeks=12,
                group_by="week"
            )

            assert len(trends) == 1
            assert "W01" in trends[0]["date"]


@pytest.mark.unit
class TestAnalyticsDailyPatterns:
    """Test daily study pattern calculation."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.execute = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_daily_patterns(self, mock_db):
        """Test getting daily study patterns."""
        user_id = uuid.uuid4()

        pattern_result = MagicMock()
        pattern_result.__iter__ = lambda self: iter([
            MagicMock(
                date="2026-01-01",
                total_minutes=60,
                session_count=3,
                notes_created=5,
                questions_answered=2,
            ),
            MagicMock(
                date="2026-01-02",
                total_minutes=30,
                session_count=1,
                notes_created=2,
                questions_answered=0,
            ),
        ])

        mock_db.execute.return_value = pattern_result

        with patch.object(AnalyticsService, '__init__', lambda self, db: None):
            service = AnalyticsService(mock_db)
            service.db = mock_db

            patterns = await service._get_daily_study_patterns(user_id, days=30)

            assert len(patterns) == 2
            assert patterns[0]["date"] == "2026-01-01"
            assert patterns[0]["total_minutes"] == 60
            assert patterns[1]["questions_answered"] == 0
