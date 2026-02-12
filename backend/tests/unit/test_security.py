"""Unit tests for security utilities."""

import pytest
from uuid import uuid4
from app.utils.security import get_password_hash, verify_password
from app.utils.jwt import create_access_token, verify_access_token


@pytest.mark.unit
class TestSecurity:
    """Test security utilities."""

    def test_password_hashing(self):
        """Test password hashing creates different hashes."""
        password = "testPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Same password should produce different hashes (salted)
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_password_verification(self):
        """Test password verification."""
        password = "testPassword123"
        hashed = get_password_hash(password)

        # Correct password
        assert verify_password(password, hashed) is True

        # Wrong password
        assert verify_password("wrongPassword", hashed) is False

    def test_jwt_token_creation(self):
        """Test JWT token creation and verification."""
        data = {"sub": str(uuid4()), "email": "test@example.com"}

        # Create token
        token = create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token
        payload = verify_access_token(token)
        assert payload["sub"] == data["sub"]
        assert payload["email"] == data["email"]
        assert "exp" in payload