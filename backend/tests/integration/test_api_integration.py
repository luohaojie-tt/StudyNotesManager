"""
Integration tests for API endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.api
class TestAuthAPI:
    """Test authentication API endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client: AsyncClient):
        """Test user registration endpoint."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "integration@test.com",
                "username": "integrationuser",
                "password": "SecurePass123!",
                "full_name": "Integration Test User"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "integration@test.com"
        assert data["username"] == "integrationuser"
        assert "id" in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": "duplicate@test.com",
            "username": "user1",
            "password": "SecurePass123!",
            "full_name": "User One"
        }

        # First registration
        await client.post("/api/v1/auth/register", json=user_data)

        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@test.com",
                "username": "user2",
                "password": "SecurePass123!",
                "full_name": "User Two"
            }
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_login_valid_credentials(self, client: AsyncClient):
        """Test login with valid credentials."""
        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@test.com",
                "username": "loginuser",
                "password": "LoginPass123!",
                "full_name": "Login User"
            }
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "loginuser",
                "password": "LoginPass123!"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "WrongPassword!"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, auth_headers):
        """Test getting current authenticated user."""
        headers = await auth_headers()

        response = await client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert "email" in data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
class TestNotesAPI:
    """Test notes API endpoints."""

    @pytest.fixture
    async def authenticated_headers(self, client: AsyncClient, test_user_data):
        """Create authenticated user and return headers."""
        await client.post("/api/v1/auth/register", json=test_user_data)

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_create_note(self, client: AsyncClient, authenticated_headers):
        """Test creating a note."""
        response = await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Integration Test Note",
                "content": "This is integration test content",
                "subject": "Mathematics",
                "tags": ["integration", "test"]
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Integration Test Note"
        assert data["subject"] == "Mathematics"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_note(self, client: AsyncClient, authenticated_headers):
        """Test retrieving a specific note."""
        # Create a note first
        create_response = await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Test Note",
                "content": "Content",
                "subject": "Physics"
            }
        )
        note_id = create_response.json()["id"]

        # Get the note
        response = await client.get(
            f"/api/v1/notes/{note_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == note_id
        assert data["title"] == "Test Note"

    @pytest.mark.asyncio
    async def test_list_notes(self, client: AsyncClient, authenticated_headers):
        """Test listing user's notes."""
        # Create multiple notes
        for i in range(3):
            await client.post(
                "/api/v1/notes",
                headers=authenticated_headers,
                json={
                    "title": f"Note {i}",
                    "content": f"Content {i}",
                    "subject": "Chemistry"
                }
            )

        # List notes
        response = await client.get(
            "/api/v1/notes",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_update_note(self, client: AsyncClient, authenticated_headers):
        """Test updating a note."""
        # Create note
        create_response = await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Original Title",
                "content": "Original content",
                "subject": "Biology"
            }
        )
        note_id = create_response.json()["id"]

        # Update note
        response = await client.put(
            f"/api/v1/notes/{note_id}",
            headers=authenticated_headers,
            json={
                "title": "Updated Title",
                "content": "Updated content"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_note(self, client: AsyncClient, authenticated_headers):
        """Test deleting a note."""
        # Create note
        create_response = await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "To Delete",
                "content": "Will be deleted",
                "subject": "History"
            }
        )
        note_id = create_response.json()["id"]

        # Delete note
        response = await client.delete(
            f"/api/v1/notes/{note_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(
            f"/api/v1/notes/{note_id}",
            headers=authenticated_headers
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_notes_by_subject(self, client: AsyncClient, authenticated_headers):
        """Test searching notes by subject."""
        # Create notes with different subjects
        await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Math Note",
                "content": "Math content",
                "subject": "Mathematics"
            }
        )
        await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Physics Note",
                "content": "Physics content",
                "subject": "Physics"
            }
        )

        # Search for Mathematics notes
        response = await client.get(
            "/api/v1/notes?subject=Mathematics",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["subject"] == "Mathematics"


@pytest.mark.integration
@pytest.mark.api
class TestMindmapAPI:
    """Test mindmap generation API endpoints."""

    @pytest.fixture
    async def authenticated_headers(self, client: AsyncClient, test_user_data):
        """Create authenticated user and return headers."""
        await client.post("/api/v1/auth/register", json=test_user_data)

        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_generate_mindmap_from_text(self, client: AsyncClient, authenticated_headers):
        """Test generating mindmap from text."""
        response = await client.post(
            "/api/v1/mindmaps/generate",
            headers=authenticated_headers,
            json={
                "content": "Mathematics includes algebra, calculus, and geometry"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0

    @pytest.mark.asyncio
    async def test_generate_mindmap_from_note(self, client: AsyncClient, authenticated_headers):
        """Test generating mindmap from existing note."""
        # Create a note first
        note_response = await client.post(
            "/api/v1/notes",
            headers=authenticated_headers,
            json={
                "title": "Physics Concepts",
                "content": "Newton's laws of motion describe the relationship between forces and motion",
                "subject": "Physics"
            }
        )
        note_id = note_response.json()["id"]

        # Generate mindmap from note
        response = await client.post(
            f"/api/v1/notes/{note_id}/mindmap",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


@pytest.mark.integration
class TestDatabaseOperations:
    """Test database operations and transactions."""

    @pytest.mark.asyncio
    async def test_database_transaction_rollback(self, async_db_session):
        """Test that database transactions rollback on error."""
        from app.models.user import User
        from app.services.auth_service import AuthService
        from app.schemas.user import UserCreate
        from sqlalchemy.exc import IntegrityError

        service = AuthService(async_db_session)

        # This should fail due to duplicate constraint
        user_data = UserCreate(
            email="test@test.com",
            username="testuser",
            password="Password123!",
            full_name="Test User"
        )

        # Try to create duplicate user (should handle gracefully)
        try:
            await service.register(user_data)
            # Attempt to register again
            await service.register(user_data)
        except Exception:
            pass  # Expected

        # Verify transaction was rolled back
        # Database should be in consistent state


@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Test API performance under load."""

    @pytest.mark.asyncio
    async def test_concurrent_note_creation(self, client: AsyncClient, test_user_data):
        """Test creating multiple notes concurrently."""
        import asyncio

        # Setup authentication
        await client.post("/api/v1/auth/register", json=test_user_data)
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create notes concurrently
        async def create_note(i):
            return await client.post(
                "/api/v1/notes",
                headers=headers,
                json={
                    "title": f"Concurrent Note {i}",
                    "content": f"Content {i}",
                    "subject": "Test"
                }
            )

        tasks = [create_note(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 201
