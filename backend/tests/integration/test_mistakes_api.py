"""
Integration tests for Mistakes API endpoints.

Tests /api/mistakes/* endpoints with real database interactions.
"""
import uuid
import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.api
class TestMistakesListAPI:
    """Test mistake list and retrieval endpoints."""

    @pytest.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="mistaketest@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Mistake Test User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_list_mistakes_empty(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test listing mistakes when none exist."""
        # Login and get token
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistaketest@test.com",
                "password": "TestPass123!"
            }
        )
        assert login_response.status_code == 200
        token_data = login_response.json()

        response = await client.get(
            "/api/mistakes",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "mistakes" in data
        assert "total" in data
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_mistakes_pagination(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test listing mistakes with pagination."""
        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistaketest@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        response = await client.get(
            "/api/mistakes",
            params={
                "skip": 0,
                "limit": 10
            },
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "mistakes" in data
        assert len(data["mistakes"]) <= 10


@pytest.mark.integration
@pytest.mark.api
class TestMistakesCreateAPI:
    """Test mistake creation endpoint."""

    @pytest.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="mistakecreate@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Mistake Create User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_create_mistake_success(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test creating a mistake successfully."""
        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakecreate@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        mistake_data = {
            "question": "What is the capital of France?",
            "correct_answer": "Paris",
            "user_answer": "London",
            "question_type": "choice",
            "subject": "Geography",
            "knowledge_points": ["Capitals", "Europe"],
            "difficulty": 2,
            "source": "Quiz 1",
            "tags": ["easy", "geography"]
        }

        response = await client.post(
            "/api/mistakes",
            json=mistake_data,
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["question"] == mistake_data["question"]
        assert data["subject"] == mistake_data["subject"]
        assert data["mastery_level"] == 0

    @pytest.mark.asyncio
    async def test_create_mistake_invalid_data(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test creating mistake with invalid data."""
        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakecreate@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        # Missing required field
        response = await client.post(
            "/api/mistakes",
            json={
                "question": "Test question",
                # Missing "subject"
            },
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.integration
@pytest.mark.api
class TestMistakesDetailAPI:
    """Test mistake detail, update, and delete endpoints."""

    @pytest.fixture
    async def test_user_with_mistake(self, async_db_session: AsyncSession):
        """Create a test user with a mistake."""
        from app.models.user import User
        from app.models.mistake import Mistake
        from app.utils.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="mistakedetail@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Mistake Detail User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)

        mistake = Mistake(
            id=uuid.uuid4(),
            user_id=user.id,
            question="What is 2+2?",
            question_type="choice",
            correct_answer="4",
            user_answer="3",
            subject="Math",
            knowledge_points=["Addition"],
            difficulty=1,
            mastery_level=0,
            review_count=0,
            correct_count=0,
            incorrect_count=0,
            consecutive_correct=0,
            is_archived=False
        )
        async_db_session.add(mistake)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user, mistake

    @pytest.mark.asyncio
    async def test_get_mistake_success(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test getting a specific mistake."""
        user, mistake = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakedetail@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        response = await client.get(
            f"/api/mistakes/{mistake.id}",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mistake.id)
        assert data["question"] == mistake.question

    @pytest.mark.asyncio
    async def test_get_mistake_not_found(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test getting non-existent mistake."""
        user, _ = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakedetail@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        response = await client.get(
            f"/api/mistakes/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_mistake(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test updating a mistake."""
        user, mistake = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakedetail@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        update_data = {
            "explanation": "This is a simple addition problem."
        }

        response = await client.put(
            f"/api/mistakes/{mistake.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["explanation"] == update_data["explanation"]

    @pytest.mark.asyncio
    async def test_delete_mistake(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test deleting a mistake."""
        user, mistake = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakedetail@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        response = await client.delete(
            f"/api/mistakes/{mistake.id}",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(
            f"/api/mistakes/{mistake.id}",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )
        assert get_response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
class TestMistakesReviewAPI:
    """Test mistake review and weak points endpoints."""

    @pytest.fixture
    async def test_user_with_mistake(self, async_db_session: AsyncSession):
        """Create a test user with a mistake."""
        from app.models.user import User
        from app.models.mistake import Mistake
        from app.utils.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="mistakereview@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Mistake Review User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)

        mistake = Mistake(
            id=uuid.uuid4(),
            user_id=user.id,
            question="What is 2+2?",
            question_type="choice",
            correct_answer="4",
            user_answer="3",
            subject="Math",
            knowledge_points=["Addition"],
            difficulty=1,
            mastery_level=0,
            review_count=0,
            correct_count=0,
            incorrect_count=0,
            consecutive_correct=0,
            next_review_at=datetime.datetime.utcnow(),
            is_archived=False
        )
        async_db_session.add(mistake)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user, mistake

    @pytest.mark.asyncio
    async def test_review_mistake_correct(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test reviewing a mistake with correct answer."""
        user, mistake = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakereview@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        review_data = {
            "is_correct": True,
            "time_spent": 30
        }

        response = await client.post(
            f"/api/mistakes/{mistake.id}/review",
            json=review_data,
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] == True
        assert data["mastery_level"] > 0  # Should increase
        assert "next_review_at" in data

    @pytest.mark.asyncio
    async def test_get_weak_points(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test getting weak points analysis."""
        user, mistake = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakereview@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        response = await client.get(
            "/api/mistakes/weak-points",
            params={"limit": 10},
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "weak_points" in data
        assert "total_mistakes" in data
        assert data["total_mistakes"] >= 1

    @pytest.mark.asyncio
    async def test_get_due_count(
        self,
        client: AsyncClient,
        test_user_with_mistake
    ):
        """Test getting due review count."""
        user, mistake = test_user_with_mistake

        # Login
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": "mistakereview@test.com",
                "password": "TestPass123!"
            }
        )
        token_data = login_response.json()

        response = await client.get(
            "/api/mistakes/due-count",
            headers={"Authorization": f"Bearer {token_data['access_token']}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "due_count" in data
        assert data["due_count"] >= 1
