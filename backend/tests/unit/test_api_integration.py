"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.mark.unit
class TestAPIIntegration:
    """Test API endpoints."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_auth_register_endpoint(self):
        """Test user registration endpoint."""
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "Test User"
        }

        response = self.client.post("/api/auth/register", json=user_data)
        # Should succeed or fail with validation error, but not 500
        assert response.status_code in [200, 400, 422]

    def test_auth_login_endpoint(self):
        """Test user login endpoint."""
        login_data = {
            "email": "test@example.com",
            "password": "SecurePass123!"
        }

        response = self.client.post("/api/auth/login", json=login_data)
        # Should succeed or fail with validation error, but not 500
        assert response.status_code in [200, 400, 422]

    def test_notes_create_endpoint(self):
        """Test note creation endpoint."""
        note_data = {
            "title": "Test Note",
            "content": "This is a test note",
            "tags": ["test", "example"]
        }

        response = self.client.post("/api/notes", json=note_data)
        # Should succeed or fail with auth error, but not 500
        assert response.status_code in [200, 401, 422]

    def test_mindmaps_generate_endpoint(self):
        """Test mindmap generation endpoint."""
        mindmap_data = {
            "content": "Main idea\n- Sub idea 1\n- Sub idea 2"
        }

        response = self.client.post("/api/mindmaps/generate", json=mindmap_data)
        # Should succeed or fail with auth error, but not 500
        assert response.status_code in [200, 401, 422]

    def test_quizzes_generate_endpoint(self):
        """Test quiz generation endpoint."""
        quiz_data = {
            "topic": "Test Topic",
            "num_questions": 5
        }

        response = self.client.post("/api/quizzes/generate", json=quiz_data)
        # Should succeed or fail with auth error, but not 500
        assert response.status_code in [200, 401, 422]