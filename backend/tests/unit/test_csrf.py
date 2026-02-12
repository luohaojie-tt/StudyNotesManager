"""CSRF protection tests."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.security import generate_csrf_token, CSRF_HEADER_NAME

client = TestClient(app)


@pytest.mark.csrf
class TestCSRFProtection:
    """Test CSRF protection middleware."""

    def test_csrf_cookie_set_on_safe_request(self):
        """Test that CSRF cookie is set on safe requests (GET)."""
        response = client.get("/")
        
        # Check that CSRF cookie is set
        assert "csrf_token" in response.cookies
        assert len(response.cookies["csrf_token"]) > 0

    def test_safe_methods_work_without_csrf_token(self):
        """Test that safe methods work without CSRF token."""
        safe_methods = [
            ("GET", "/"),
            ("GET", "/health"),
        ]
        
        for method, endpoint in safe_methods:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.request(method, endpoint)
            
            # Safe methods should work
            assert response.status_code != 403

    def test_post_without_csrf_token_returns_403(self):
        """Test that POST without CSRF token returns 403."""
        # First, get a CSRF token via GET request
        get_response = client.get("/")
        csrf_token = get_response.cookies.get("csrf_token")
        
        # Try POST without CSRF header
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            }
        )
        
        # Should fail with 403
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"].lower()

    def test_post_with_invalid_csrf_token_returns_403(self):
        """Test that POST with invalid CSRF token returns 403."""
        # Get CSRF token from cookie
        get_response = client.get("/")
        cookie_token = get_response.cookies.get("csrf_token")
        
        # Try POST with different token in header
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpass123"
            },
            headers={CSRF_HEADER_NAME: "invalid_token_12345"}
        )
        
        # Should fail with 403
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"].lower()

    def test_post_with_valid_csrf_token_succeeds(self):
        """Test that POST with valid CSRF token succeeds."""
        # Get CSRF token from cookie
        get_response = client.get("/")
        csrf_token = get_response.cookies.get("csrf_token")
        
        # Try POST with valid CSRF header
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser_csrf",
                "email": "csrf_test@example.com",
                "password": "testpass123"
            },
            headers={CSRF_HEADER_NAME: csrf_token}
        )
        
        # Should either succeed or fail with validation error (not CSRF error)
        # Status code should NOT be 403
        assert response.status_code != 403

    def test_put_without_csrf_token_returns_403(self):
        """Test that PUT without CSRF token returns 403."""
        # Get CSRF token first
        client.get("/")
        
        # Try PUT without CSRF header (this will fail with 404, but should be 403 for CSRF)
        response = client.put(
            "/api/notes/test-id",
            json={"title": "Test"}
        )
        
        # Should fail with 403 for CSRF, not 404
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"].lower()

    def test_delete_without_csrf_token_returns_403(self):
        """Test that DELETE without CSRF token returns 403."""
        # Get CSRF token first
        client.get("/")
        
        # Try DELETE without CSRF header
        response = client.delete("/api/notes/test-id")
        
        # Should fail with 403 for CSRF
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"].lower()

    def test_csrf_token_persists_across_requests(self):
        """Test that CSRF token remains the same across requests."""
        # First request
        response1 = client.get("/")
        token1 = response1.cookies.get("csrf_token")
        
        # Second request
        response2 = client.get("/")
        token2 = response2.cookies.get("csrf_token")
        
        # Tokens should be the same (cookie persists)
        assert token1 == token2

    def test_csrf_token_format(self):
        """Test that CSRF token has correct format."""
        response = client.get("/")
        token = response.cookies.get("csrf_token")
        
        # Token should be alphanumeric
        assert token.isalnum()
        # Token should be 32 characters long (as configured)
        assert len(token) == 32


@pytest.mark.csrf
class TestCSRFGeneric:
    """Test CSRF token generation utilities."""

    def test_generate_csrf_token(self):
        """Test CSRF token generation."""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        
        # Tokens should be different
        assert token1 != token2
        
        # Tokens should be correct length
        assert len(token1) == 32
        assert len(token2) == 32
        
        # Tokens should be alphanumeric
        assert token1.isalnum()
        assert token2.isalnum()
