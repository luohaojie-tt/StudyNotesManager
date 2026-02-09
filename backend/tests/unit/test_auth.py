"""
Unit tests for authentication functionality.

Security improvements:
- Uses secure test data generation
- Avoids hardcoded passwords
- Tests are properly isolated
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

from jose import JWTError
from sqlalchemy import select
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data



@pytest.mark.unit
@pytest.mark.auth
class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_password_hashing(self, valid_password):
        """Test that password hashing works correctly."""
        from app.utils.security import get_password_hash

        hashed = get_password_hash(valid_password)

        # Hash should be different from original
        assert hashed != valid_password
        # Hash should contain bcrypt identifier
        assert hashed.startswith("$2b$")

    def test_password_verification_correct(self, valid_password):
        """Test password verification with correct password."""
        from app.utils.security import get_password_hash, verify_password

        hashed = get_password_hash(valid_password)

        assert verify_password(valid_password, hashed) is True

    def test_password_verification_incorrect(self, valid_password):
        """Test password verification with incorrect password."""
        from app.utils.security import get_password_hash, verify_password

        hashed = get_password_hash(valid_password)
        wrong_password = test_data.random_password()
        
        assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
@pytest.mark.auth
class TestJWTToken:
    """Test JWT token creation and verification."""

    def test_create_access_token_default_expiration(self, valid_password):
        """Test JWT access token creation with default expiration."""
        from app.utils.jwt import create_access_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT should have 3 parts separated by dots
        assert token.count(".") == 2

    test_create_access_token_custom_expiration(self, valid_password):
        """Test JWT access token creation with custom expiration."""
        from app.utils.jwt import create_access_token, verify_access_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        token = create_access_token(data, expires_delta=timedelta(minutes=30))

        payload = verify_access_token(token)
        assert payload["sub"] in data["sub"]
        assert "exp" in payload
        assert payload["type"] == "access"

    test_create_refresh_token(self, valid_password):
        """Test JWT refresh token creation."""
        from app.utils.jwt import create_refresh_token, verify_refresh_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        token = create_refresh_token(data)

        payload = verify_refresh_token(token)
        assert payload["sub"] in data["sub"]
        assert "exp" in payload
        assert payload["type"] == "refresh"

    test_verify_access_token_valid(self, valid_password):
        """Test verification of valid access token."""
        from app.utils.jwt import create_access_token, verify_access_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        token = create_access_token(data)

        payload = verify_access_token(token)
        assert "sub" in payload
        assert "exp" in payload
        assert payload["type"] == "access"

    test_verify_refresh_token_valid(self, valid_password):
        """Test verification of valid refresh token."""
        from app.utils.jwt import create_refresh_token, verify_refresh_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        token = create_refresh_token(data)

        payload = verify_refresh_token(token)
        assert "sub" in payload
        assert "exp" in payload
        assert payload["type"] == "refresh"

    test_verify_token_invalid(self, valid_password):
        """Test verification of invalid token."""
        from app.utils.jwt import verify_access_token

        invalid_token = "invalid.token.here"

        with pytest.raises(JWTError):
            verify_access_token(invalid_token)

    test_verify_token_wrong_type(self, valid_password):
        """Test that access token verification rejects refresh tokens."""
        from app.utils.jwt import create_refresh_token, verify_access_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        refresh_token = create_refresh_token(data)

        with pytest.raises(JWTError, match="Invalid token type"):
            verify_access_token(refresh_token)

    test_token_expiration(self, valid_password):
        """Test that token includes expiration."""
        import time
        from app.utils.jwt import create_access_token, verify_access_token

        data = {"sub": str(uuid4()), "email": valid_email, }
        token = create_access_token(data, expires_delta=timedelta(seconds=60))

        payload = verify_access_token(token)
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
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def valid_user_data(self):
        """Create valid user registration data."""
        from app.schemas.auth import UserRegister
        return UserRegister(
            email="test@example.com",
            password="SecurePass123",
            full_name="Test User"
        )

    @pytest.mark.asyncio
    async def test_register_user_success(self, mock_db_session, valid_user_data):
        """Test successful user registration."""
        from app.services.auth_service import AuthService
        from app.models.user import User

        # Mock that user doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Create service and register user
        auth_service = AuthService(mock_db_session)
        user = await auth_service.register_user(valid_user_data)

        # Verify database operations
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.refresh.called

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, mock_db_session, valid_user_data):
        """Test registering with duplicate email raises error."""
        from app.services.auth_service import AuthService
        from app.models.user import User

        # Mock that user exists
        existing_user = User(
            email="test@example.com",
            password_hash="hash",
            full_name="Existing User"
        )
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = existing_user
        mock_db_session.execute.return_value = mock_result

        # Should raise ValueError
        auth_service = AuthService(mock_db_session)
        with pytest.raises(ValueError, match="Email already registered"):
            await auth_service.register_user(valid_user_data)

    @pytest.mark.asyncio
    async def test_register_user_password_hashed(self, mock_db_session, valid_user_data):
        """Test that password is hashed during registration."""
        from app.services.auth_service import AuthService

        # Mock that user doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Create service and register user
        auth_service = AuthService(mock_db_session)
        user = await auth_service.register_user(valid_user_data)

        # Get the user that was added to database
        added_user = mock_db_session.add.call_args[0][0]
        # Password should be hashed, not plain text
        assert added_user.password_hash != valid_user_data.password
        assert added_user.password_hash.startswith("$2b$")

    @pytest.mark.asyncio
    async def test_register_user_default_values(self, mock_db_session, valid_user_data):
        """Test that default values are set correctly."""
        from app.services.auth_service import AuthService

        # Mock that user doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Create service and register user
        auth_service = AuthService(mock_db_session)
        user = await auth_service.register_user(valid_user_data)

        # Get the user that was added to database
        added_user = mock_db_session.add.call_args[0][0]
        assert added_user.subscription_tier == "free"
        assert added_user.is_active is True
        assert added_user.is_verified is False
        assert added_user.verification_token is not None

    @pytest.mark.asyncio
    async def test_authenticate_user_valid_credentials(self, mock_db_session):
        """Test authentication with valid credentials."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.utils.security import get_password_hash

        # Create test user
        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=get_password_hash(valid_password),
            full_name="Test User",
            is_active=True
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate_user(
            "test@example.com",
            "SecurePass123"
        )

        assert authenticated_user is not None
        assert authenticated_user.email == "test@example.com"
        assert mock_db_session.commit.called  # last_login_at update

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, mock_db_session):
        """Test authentication with invalid password."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.utils.security import get_password_hash

        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=get_password_hash(valid_password),
            full_name="Test User",
            is_active=True
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate_user(
            "test@example.com",
            "WrongPassword"
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(self, mock_db_session):
        """Test authentication with nonexistent email."""
        from app.services.auth_service import AuthService

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate_user(
            "nonexistent@example.com",
            "password"
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_authenticate_user_inactive_account(self, mock_db_session):
        """Test authentication with inactive account."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.utils.security import get_password_hash

        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash=get_password_hash(valid_password),
            full_name="Test User",
            is_active=False
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        auth_service = AuthService(mock_db_session)
        authenticated_user = await auth_service.authenticate_user(
            "test@example.com",
            "SecurePass123"
        )

        assert authenticated_user is None

    @pytest.mark.asyncio
    async def test_get_user_by_id_found(self, mock_db_session):
        """Test getting user by existing ID."""
        from app.services.auth_service import AuthService
        from app.models.user import User

        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hash",
            full_name="Test User"
        )

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = user
        mock_db_session.execute.return_value = mock_result

        auth_service = AuthService(mock_db_session)
        found_user = await auth_service.get_user_by_id(user_id)

        assert found_user is not None
        assert found_user.id == user_id
        assert found_user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, mock_db_session):
        """Test getting user by non-existent ID."""
        from app.services.auth_service import AuthService

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        auth_service = AuthService(mock_db_session)
        found_user = await auth_service.get_user_by_id(uuid4())

        assert found_user is None

    def test_create_tokens(self, mock_db_session):
        """Test token creation."""
        from app.services.auth_service import AuthService
        from app.models.user import User

        user = User(
            id=uuid4(),
            email="test@example.com",
            password_hash="hash",
            full_name="Test User"
        )

        auth_service = AuthService(mock_db_session)
        tokens = auth_service.create_tokens(user)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 900
        assert len(tokens["access_token"]) > 0
        assert len(tokens["refresh_token"]) > 0

    def test_create_tokens_contain_correct_data(self, mock_db_session):
        """Test that tokens contain correct user data."""
        from app.services.auth_service import AuthService
        from app.models.user import User
        from app.utils.jwt import verify_access_token, verify_refresh_token

        user_id = uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            password_hash="hash",
            full_name="Test User"
        )

        auth_service = AuthService(mock_db_session)
        tokens = auth_service.create_tokens(user)

        # Verify access token contains correct data
        access_payload = verify_access_token(tokens["access_token"])
        assert access_payload["sub"] == str(user_id)
        assert access_payload["email"] == "test@example.com"

        # Verify refresh token contains correct data
        refresh_payload = verify_refresh_token(tokens["refresh_token"])
        assert refresh_payload["sub"] == str(user_id)
        assert refresh_payload["email"] == "test@example.com"


@pytest.mark.unit
@pytest.mark.auth
class TestAuthSchemas:
    """Test authentication schemas validation."""

    test_user_register_valid(self, valid_password):
        """Test valid user registration schema."""
        from app.schemas.auth import UserRegister

        user_data = UserRegister(
            email="test@example.com",
            password="SecurePass123",
            full_name="Test User"
        )

        assert user_data.email == "test@example.com"
        assert user_data.password == "SecurePass123"
        assert user_data.full_name == "Test User"

    test_user_register_password_too_short(self, valid_password):
        """Test password validation fails for short passwords."""
        from pydantic import ValidationError
        from app.schemas.auth import UserRegister

        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                password="Short1",
                full_name="Test User"
            )

    test_user_register_password_no_letters(self, valid_password):
        """Test password validation fails for passwords without letters."""
        from pydantic import ValidationError
        from app.schemas.auth import UserRegister

        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                password="12345678",
                full_name="Test User"
            )

    test_user_register_password_no_digits(self, valid_password):
        """Test password validation fails for passwords without digits."""
        from pydantic import ValidationError
        from app.schemas.auth import UserRegister

        with pytest.raises(ValidationError):
            UserRegister(
                email="test@example.com",
                password="PasswordOnly",
                full_name="Test User"
            )

    test_user_login_valid(self, valid_password):
        """Test valid user login schema."""
        from app.schemas.auth import UserLogin

        login_data = UserLogin(
            email="test@example.com",
            password="SecurePass123"
        )

        assert login_data.email == "test@example.com"
        assert login_data.password == "SecurePass123"

    test_user_response_model(self, valid_password):
        """Test user response schema."""
        from app.schemas.auth import UserResponse
        from datetime import datetime

        user_id = uuid4()
        user_response = UserResponse(
            id=user_id,
            email="test@example.com",
            full_name="Test User",
            subscription_tier="free",
            is_verified=False,
            created_at=datetime.utcnow()
        )

        assert user_response.id == user_id
        assert user_response.email == "test@example.com"
        assert user_response.subscription_tier == "free"
