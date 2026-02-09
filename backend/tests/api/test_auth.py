"""Authentication API tests."""
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app


class TestAuthenticationEndpoints:
    """Test authentication endpoints."""

    def test_register_new_user(self, client: AsyncClient):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test2@example.com",
                "password": "weak",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 422

    def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration with duplicate email."""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )

        # Duplicate registration
        response = client.post(
            "/api/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )
        assert response.status_code == 400

    def test_login_valid_credentials(self, client: AsyncClient):
        """Test login with valid credentials."""
        # Register first
        client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )

        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@example.com",
                "password": "TestPassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "WrongPassword123",
            },
        )
        assert response.status_code == 401

    def test_get_current_user(self, client: AsyncClient):
        """Test getting current user info."""
        # Register and login
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "me@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )
        token = register_response.json()["access_token"]

        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["full_name"] == "Test User"

    def test_get_current_user_without_token(self, client: AsyncClient):
        """Test getting current user without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_refresh_token(self, client: AsyncClient):
        """Test token refresh."""
        # Register
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )
        refresh_token = register_response.json()["refresh_token"]

        # Refresh token
        response = client.post(
            "/api/auth/refresh-token",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_logout(self, client: AsyncClient):
        """Test logout."""
        # Register
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "logout@example.com",
                "password": "TestPassword123",
                "full_name": "Test User",
            },
        )
        token = register_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
