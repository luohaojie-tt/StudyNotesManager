"""
Integration tests for Quizzes API endpoints.

Tests the /api/quizzes/* endpoints with real database interactions.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.api
class TestQuizzesListAPI:
    """Test quiz list and retrieval endpoints."""

    @pytest.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="quizlist@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Quiz List Test User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_list_quizzes_empty(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test listing quizzes when none exist."""
        response = await client.get(
            "/api/quizzes",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert "quizzes" in data
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_quizzes_pagination(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test listing quizzes with pagination parameters."""
        response = await client.get(
            "/api/quizzes",
            params={
                "user_id": str(test_user.id),
                "skip": 0,
                "limit": 10
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "quizzes" in data
        assert len(data["quizzes"]) <= 10


@pytest.mark.integration
@pytest.mark.api
class TestQuizStatsAPI:
    """Test quiz statistics API."""

    @pytest.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="quizstats@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Quiz Stats Test User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_get_quiz_stats_empty(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test getting quiz statistics when no quizzes exist."""
        response = await client.get(
            "/api/quizzes/stats/overview",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_quizzes"] == 0
        assert data["completed_quizzes"] == 0
        assert data["average_score"] == 0.0
