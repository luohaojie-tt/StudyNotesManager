"""Unit tests for auth service functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4
from datetime import datetime

from app.services.auth_service import AuthService
from app.schemas.auth import UserRegister


@pytest.mark.unit
class TestAuthService:
    """Test AuthService methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.add = Mock()
        return db

    @pytest.fixture
    def auth_service(self, mock_db):
        """Create auth service with mock DB."""
        return AuthService(mock_db)

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_db):
        """Test successful user registration."""
        from app.models.user import User

        # Mock the Result object returned by execute
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        user_data = UserRegister(
            email="test@example.com",
            password="Pass1234",  # Meets 8 char min, letter + number
            full_name="Test User"
        )

        # Track added user
        added_user = None

        def side_effect_add(user):
            nonlocal added_user
            added_user = user
            # Set an ID for the user
            user.id = uuid4()

        async def side_effect_refresh(user):
            pass  # Don't modify the user

        mock_db.add.side_effect = side_effect_add
        mock_db.refresh.side_effect = side_effect_refresh

        result = await auth_service.register_user(user_data)

        # Verify database calls
        assert mock_db.execute.call_count == 1
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

        assert result.email == "test@example.com"
        assert result.full_name == "Test User"
        assert result.is_active is True
        assert result.is_verified is False

    @pytest.mark.asyncio
    async def test_register_user_existing_email(self, auth_service, mock_db):
        """Test registration fails with existing email."""
        from app.models.user import User

        # Mock existing user
        mock_user = User(
            id=uuid4(),
            email="existing@example.com",
            password_hash="hash",
            is_active=True,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        user_data = UserRegister(
            email="existing@example.com",
            password="Pass1234",
            full_name="Test User"
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful user authentication."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        password = "Pass1234"
        password_hash = get_password_hash(password)

        mock_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await auth_service.authenticate_user("test@example.com", password)

        assert result is not None
        assert result.email == "test@example.com"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, auth_service, mock_db):
        """Test authentication fails with wrong password."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        password_hash = get_password_hash("CorrectPass123")

        mock_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await auth_service.authenticate_user(
            "test@example.com", "WrongPass123"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, auth_service, mock_db):
        """Test authentication fails when user not found."""

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await auth_service.authenticate_user(
            "nonexistent@example.com", "Pass1234"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_db):
        """Test authentication fails for inactive user."""
        from app.models.user import User
        from app.utils.security import get_password_hash

        password_hash = get_password_hash("Pass1234")

        mock_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=password_hash,
            is_active=False,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await auth_service.authenticate_user("test@example.com", "Pass1234")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, auth_service, mock_db):
        """Test getting user by ID."""
        from app.models.user import User

        user_id = uuid4()
        mock_user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hash",
            is_active=True,
            created_at=datetime.utcnow()
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result

        result = await auth_service.get_user_by_id(user_id)

        assert result is not None
        assert result.id == user_id
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, auth_service, mock_db):
        """Test getting user by ID when not found."""

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await auth_service.get_user_by_id(uuid4())

        assert result is None

    def test_create_tokens(self, auth_service):
        """Test token creation."""
        from app.models.user import User

        mock_user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash",
            is_active=True,
            created_at=datetime.utcnow()
        )

        tokens = auth_service.create_tokens(mock_user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert "expires_in" in tokens
        assert isinstance(tokens["access_token"], str)
        assert isinstance(tokens["refresh_token"], str)
        assert len(tokens["access_token"]) > 0
        assert len(tokens["refresh_token"]) > 0
