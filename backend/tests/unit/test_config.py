"""Unit tests for configuration utilities."""

import pytest
from app.core.config import settings


@pytest.mark.unit
class TestConfig:
    """Test configuration settings."""

    def test_app_settings(self):
        """Test basic app settings."""
        assert settings.APP_NAME == "Study Notes Manager"
        assert settings.VERSION == "1.0.0"
        assert settings.DEBUG is False

    def test_database_settings(self):
        """Test database configuration."""
        assert settings.DATABASE_URL.startswith("sqlite")
        assert "/db" in settings.DATABASE_URL

    def test_security_settings(self):
        """Test security settings."""
        assert isinstance(settings.SECRET_KEY, str)
        assert len(settings.SECRET_KEY) > 0
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_rate_limit_settings(self):
        """Test rate limiting configuration."""
        assert settings.RATE_LIMIT_REQUESTS > 0
        assert settings.RATE_LIMIT_WINDOW > 0

    def test_upload_settings(self):
        """Test file upload settings."""
        assert settings.MAX_UPLOAD_SIZE > 0
        assert isinstance(settings.ALLOWED_EXTENSIONS, list)
        assert len(settings.ALLOWED_EXTENSIONS) > 0
        assert "pdf" in settings.ALLOWED_EXTENSIONS