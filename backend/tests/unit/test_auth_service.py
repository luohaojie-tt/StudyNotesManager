"""Unit tests for auth service functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.auth_service import AuthService
from app.schemas.auth import UserRegister


@pytest.mark.unit
class TestAuthService:
    """Test AuthService methods."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = AsyncMock()
        self.auth_service = AuthService(self.mock_db)

    @pytest.mark.asyncio
    async def test_register_user_success(self):
        """Test successful user registration."""
        from app.models.user import User

        # Mock database response
        self.mock_db.execute = AsyncMock()
        self.mock_db.commit = AsyncMock()
        self.mock_db.refresh = AsyncMock()

        # Mock no existing user
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = None

        user_data = UserRegister(
            email="test@example.com",
            password="SecurePass123!",
            full_name="Test User"
        )

        # Mock user creation
        mock_user = MagicMock()
        mock_user.id = uuid4()
        self.mock_db.refresh.return_value = mock_user

        result = await self.auth_service.register_user(user_data)

        # Verify database calls
        self.mock_db.execute.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_register_user_existing_email(self):
        """Test registration fails with existing email."""
        from app.models.user import User

        # Mock existing user
        mock_user = User()
        self.mock_db.execute = AsyncMock()
        self.mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

        user_data = UserRegister(
            email="existing@example.com",
            password="SecurePass123",
            full_name="Test User"
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await self.auth_service.register_user(user_data)