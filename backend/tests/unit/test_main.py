"""Unit tests for main application."""

import pytest
from fastapi import FastAPI
from app.main import app


@pytest.mark.unit
class TestMainApp:
    """Test main FastAPI application."""

    def test_app_creation(self):
        """Test that the FastAPI app is created correctly."""
        assert isinstance(app, FastAPI)
        assert app.title == "Study Notes Manager API"
        assert app.version == "1.0.0"

    def test_app_routes_exist(self):
        """Test that main routes are registered."""
        routes = [route.path for route in app.routes]

        # Check for API routes
        assert "/api/health" in routes
        assert "/api/auth" in routes
        assert "/api/notes" in routes
        assert "/api/mindmaps" in routes
        assert "/api/quizzes" in routes

    def test_middleware_configuration(self):
        """Test that middleware is properly configured."""
        # Test that CORS middleware is applied
        cors_middleware = None
        for middleware in app.user_middleware:
            if "CORSMiddleware" in str(middleware.cls):
                cors_middleware = middleware
                break

        assert cors_middleware is not None

    def test_exception_handlers(self):
        """Test that exception handlers are registered."""
        assert app.exception_handlers is not None
        assert len(app.exception_handlers) > 0