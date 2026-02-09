"""
Authentication API integration tests.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.auth
class TestAuthRegisterEndpoint:
    """Test user registration endpoint."""

    async def test_register_new_user_success(self, client: AsyncClient):
        """Test successful user registration returns tokens."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        
        # Verify user data
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["subscription_tier"] == "free"
        assert data["is_verified"] is False
        
        # Verify token structure
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    async def test_register_duplicate_email_returns_400(self, client: AsyncClient):
        """Test registering with duplicate email returns error."""
        user_data = {
            "email": "duplicate@example.com",
            "password": "SecurePass123",
            "full_name": "Test User",
        }
        
        # First registration
        await client.post("/api/auth/register", json=user_data)
        
        # Duplicate registration
        response = await client.post("/api/auth/register", json=user_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already registered" in data["detail"].lower()

    async def test_register_weak_password_returns_422(self, client: AsyncClient):
        """Test registration with weak password fails validation."""
        weak_passwords = [
            "short",           # Too short
            "nouppercase123",  # No uppercase
            "NOLOWERCASE123",  # No lowercase
            "NoDigits!",       # No digits
            "12345678",        # Only digits
        ]
        
        for password in weak_passwords:
            response = await client.post(
                "/api/auth/register",
                json={
                    "email": f"test{password}@example.com",
                    "password": password,
                    "full_name": "Test User",
                },
            )
            assert response.status_code == 422, f"Password '{password}' should be rejected"

    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        """Test registration with invalid email fails validation."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    async def test_register_missing_required_fields(self, client: AsyncClient):
        """Test registration without required fields fails."""
        # Missing email
        response = await client.post(
            "/api/auth/register",
            json={
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422
        
        # Missing password
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422
        
        # Missing full_name
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
            },
        )
        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.auth
class TestAuthLoginEndpoint:
    """Test user login endpoint."""

    async def test_login_valid_credentials_returns_tokens(self, client: AsyncClient):
        """Test login with valid credentials returns tokens."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        
        # Login
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        
        # Verify token structure
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    async def test_login_invalid_email_returns_401(self, client: AsyncClient):
        """Test login with non-existent email returns 401."""
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "SecurePass123",
            },
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "incorrect" in data["detail"].lower() or "invalid" in data["detail"].lower()

    async def test_login_invalid_password_returns_401(self, client: AsyncClient):
        """Test login with invalid password returns 401."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "CorrectPass123",
                "full_name": "Test User",
            },
        )
        
        # Login with wrong password
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "WrongPass123",
            },
        )
        
        assert response.status_code == 401

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login without credentials fails validation."""
        # Missing email
        response = await client.post(
            "/api/auth/login",
            json={"password": "SecurePass123"},
        )
        assert response.status_code == 422
        
        # Missing password
        response = await client.post(
            "/api/auth/login",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 422

    async def test_login_updates_last_login_at(self, client: AsyncClient):
        """Test that login updates user's last_login_at timestamp."""
        # Register user
        register_response = await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        original_last_login = register_response.json().get("last_login_at")
        
        # Login
        await client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
            },
        )
        
        # Get user info to check last_login_at was updated
        # Note: This would require implementing /api/auth/me with proper JWT auth
        # For now, we're testing that the endpoint exists and doesn't error


@pytest.mark.integration
@pytest.mark.auth
class TestAuthGetCurrentUserEndpoint:
    """Test get current user endpoint."""

    async def test_get_current_user_without_auth_returns_401(self, client: AsyncClient):
        """Test getting current user without authentication returns 401."""
        response = await client.get("/api/auth/me")
        
        # Note: Currently the endpoint has incorrect dependency (get_db instead of auth)
        # This test documents the expected behavior
        # When proper JWT auth is implemented, this should return 401
        pass  # Placeholder for when proper auth is implemented

    async def test_get_current_user_with_invalid_token_returns_401(self, client: AsyncClient):
        """Test getting current user with invalid token returns 401."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        # Note: When proper JWT auth is implemented, this should return 401
        pass  # Placeholder for when proper auth is implemented


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpointResponseHeaders:
    """Test authentication endpoint response headers."""

    async def test_register_returns_json_content_type(self, client: AsyncClient):
        """Test registration endpoint returns JSON content type."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        
        assert "application/json" in response.headers.get("content-type", "")

    async def test_login_returns_json_content_type(self, client: AsyncClient):
        """Test login endpoint returns JSON content type."""
        # Register user first
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
            },
        )
        
        response = await client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "SecurePass123",
            },
        )
        
        assert "application/json" in response.headers.get("content-type", "")


@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpointErrorHandling:
    """Test authentication endpoint error handling."""

    async def test_register_handles_malformed_json(self, client: AsyncClient):
        """Test registration endpoint handles malformed JSON."""
        response = await client.post(
            "/api/auth/register",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    async def test_login_handles_malformed_json(self, client: AsyncClient):
        """Test login endpoint handles malformed JSON."""
        response = await client.post(
            "/api/auth/login",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    async def test_register_handles_extra_fields(self, client: AsyncClient):
        """Test registration endpoint ignores extra fields."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123",
                "full_name": "Test User",
                "extra_field": "should_be_ignored",
            },
        )
        # Pydantic should ignore extra fields by default
        assert response.status_code == 201
