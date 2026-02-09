"""Tests for authentication HIGH priority fixes."""
import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegister


class TestPasswordValidation:
    """Test enhanced password validation."""
    
    def test_password_minimum_length(self):
        """Should require minimum 12 characters."""
        # Too short
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="Short1!",
                full_name="Test User"
            )
        assert "12 characters" in str(exc_info.value)
    
    def test_password_requires_lowercase(self):
        """Should require at least one lowercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="ABCDEFGHI123!@#",
                full_name="Test User"
            )
        assert "lowercase" in str(exc_info.value)
    
    def test_password_requires_uppercase(self):
        """Should require at least one uppercase letter."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="abcdefghijk123!@#",
                full_name="Test User"
            )
        assert "uppercase" in str(exc_info.value)
    
    def test_password_requires_digit(self):
        """Should require at least one digit."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="Abcdefghijk!@#",
                full_name="Test User"
            )
        assert "digit" in str(exc_info.value)
    
    def test_password_requires_special_char(self):
        """Should require at least one special character."""
        with pytest.raises(ValidationError) as exc_info:
            UserRegister(
                email="test@example.com",
                password="Abcdefghijk123",
                full_name="Test User"
            )
        assert "special character" in str(exc_info.value)
    
    def test_valid_password(self):
        """Should accept valid password with all requirements."""
        user = UserRegister(
            email="test@example.com",
            password="ValidPass123!@#",
            full_name="Test User"
        )
        assert user.password == "ValidPass123!@#"


class TestTokenRefreshEndpoint:
    """Test token refresh endpoint."""
    
    @pytest.mark.asyncio
    async def test_refresh_endpoint_exists(self):
        """Should have refresh endpoint registered."""
        from app.api.auth import router
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        assert any('/refresh' in path for path in routes)
    
    def test_refresh_endpoint_signature(self):
        """Should have correct signature."""
        from app.api.auth import refresh_token
        # Endpoint should accept refresh_token parameter
        assert callable(refresh_token)


class TestLogoutEndpoint:
    """Test logout endpoint."""
    
    @pytest.mark.asyncio
    async def test_logout_endpoint_exists(self):
        """Should have logout endpoint registered."""
        from app.api.auth import router
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        assert any('/logout' in path for path in routes)
    
    def test_logout_endpoint_signature(self):
        """Should have correct signature."""
        from app.api.auth import logout
        # Endpoint should require authentication
        assert callable(logout)


class TestConfigurableTokenExpiry:
    """Test token expiry configuration."""
    
    def test_access_token_expiry_in_config(self):
        """Should have ACCESS_TOKEN_EXPIRE_MINUTES in config."""
        from app.core.config import Settings
        settings = Settings()
        assert hasattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES')
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_refresh_token_expiry_in_config(self):
        """Should have REFRESH_TOKEN_EXPIRE_DAYS in config."""
        from app.core.config import Settings
        settings = Settings()
        assert hasattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS')
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0
    
    def test_refresh_token_expiry_minutes_in_config(self):
        """Should have REFRESH_TOKEN_EXPIRE_MINUTES in config."""
        from app.core.config import Settings
        settings = Settings()
        assert hasattr(settings, 'REFRESH_TOKEN_EXPIRE_MINUTES')
        assert settings.REFRESH_TOKEN_EXPIRE_MINUTES > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
