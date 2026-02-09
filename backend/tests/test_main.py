"""Test main application endpoints"""
from fastapi.testclient import TestClient

from app.main import app
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data


client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
