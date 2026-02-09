"""
Unit tests for authentication functionality.
"""
import pytest
from unittest.mock import MagicMock
from passlib.context import CryptContext


@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing(self):
        """Test that password hashing works correctly."""
        from app.core.security import get_password_hash

        password = "SecurePass123!"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password
        # Hash should contain bcrypt identifier
        assert hashed.startswith("$2b$")

    def test_password_verification_correct(self):
        """Test password verification with correct password."""
        from app.core.security import get_password_hash, verify_password

        password = "SecurePass123!"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_verification_incorrect(self):
        """Test password verification with incorrect password."""
        from app.core.security import get_password_hash, verify_password

        password = "SecurePass123!"
        wrong_password = "WrongPass456!"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
@pytest.mark.auth
class TestJWTToken:
    """Test JWT token creation and verification."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        from app.core.security import create_access_token

        data = {"sub": "testuser"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT should have 3 parts separated by dots
        assert token.count(".") == 2

    def test_verify_token_valid(self):
        """Test verification of valid token."""
        from app.core.security import create_access_token, verify_token

        data = {"sub": "testuser"}
        token = create_access_token(data)

        payload = verify_token(token)
        assert payload["sub"] == "testuser"
        assert "exp" in payload

    def test_verify_token_invalid(self):
        """Test verification of invalid token."""
        from app.core.security import verify_token

        invalid_token = "invalid.token.here"

        with pytest.raises(Exception):
            verify_token(invalid_token)

    def test_token_expiration(self):
        """Test that token includes expiration."""
        import time
        from app.core.security import create_access_token, verify_token

        data = {"sub": "testuser"}
        token = create_access_token(data, expires_delta=60)

        payload = verify_token(token)
        # Check that expiration is set to approximately 60 seconds from now
        exp_time = payload["exp"]
        current_time = int(time.time())
        assert exp_time > current_time
        assert exp_time <= current_time + 70  # Allow some margin


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test authentication service methods."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.execute = MagicMock()
        session.scalar = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        return session

    @pytest.mark.asyncio
    async def test_register_new_user(self, mock_db_session):
        """Test registering a new user."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.schemas.user import UserCreate

        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="Test User"
        )

        # Mock that user doesn't exist
        mock_db_session.scalar.return_value = None

        # Create service and register user
        auth_service = AuthService(mock_db_session)
        user = await auth_service.register(user_data)

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.hashed_password != "SecurePass123!"

    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, mock_db_session):
        """Test registering a duplicate user raises error."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.schemas.user import UserCreate
        from app.core.exceptions import DuplicateUserError

        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            password="SecurePass123!",
            full_name="Test User"
        )

        # Mock that user exists
        mock_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hash"
        )
        mock_db_session.scalar.return_value = mock_user

        # Should raise error
        auth_service = AuthService(mock_db_session)
        with pytest.raises(DuplicateUserError):
            await auth_service.register(user_data)

    @pytest.mark.asyncio
    async def test_authenticate_valid_credentials(self, mock_db_session):
        """Test authentication with valid credentials."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("SecurePass123!")
        )
        mock_db_session.scalar.return_value = user

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate(
            "testuser",
            "SecurePass123!"
        )

        assert authenticated_user is not None
        assert authenticated_user.username == "testuser"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_password(self, mock_db_session):
        """Test authentication with invalid password."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("SecurePass123!")
        )
        mock_db_session.scalar.return_value = user

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate(
            "testuser",
            "WrongPassword!"
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, mock_db_session):
        """Test authentication with nonexistent user."""
        from app.services.auth_service import AuthService

        mock_db_session.scalar.return_value = None

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate(
            "nonexistent",
            "password"
        )

        assert authenticated_user is None
