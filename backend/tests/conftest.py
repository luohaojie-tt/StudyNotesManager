"""
Pytest configuration and shared fixtures for StudyNotesManager tests.
"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool


# Environment setup for testing
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["SECRET_KEY"] = "test-secret-key-for-jwt-token-generation"
os.environ["DEEPSEEK_API_KEY"] = "test-deepseek-api-key"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    
    Uses in-memory SQLite for fast tests.
    """
    from app.core.database import Base, get_db
    
    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def client(async_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing API endpoints.
    """
    from app.main import app
    from app.core.database import get_db
    
    # Override database dependency
    async def override_get_db():
        yield async_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create async client
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def mock_redis() -> MagicMock:
    """Mock Redis client."""
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    redis_mock.exists = AsyncMock(return_value=False)
    return redis_mock


@pytest.fixture
def mock_deepseek_api() -> AsyncMock:
    """Mock DeepSeek API client."""
    api_mock = AsyncMock()
    api_mock.generate_quiz = AsyncMock(return_value={
        "questions": [
            {
                "id": "q1",
                "question": "Test question?",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "A",
                "explanation": "Test explanation"
            }
        ]
    })
    api_mock.generate_mindmap = AsyncMock(return_value={
        "nodes": [
            {"id": "n1", "label": "Concept 1", "level": 0}
        ],
        "edges": []
    })
    return api_mock


@pytest.fixture
def mock_ocr_service() -> AsyncMock:
    """Mock OCR service."""
    ocr_mock = AsyncMock()
    ocr_mock.extract_text = AsyncMock(return_value={
        "text": "Sample extracted text from image",
        "confidence": 0.95
    })
    return ocr_mock


@pytest.fixture
def mock_chromadb() -> MagicMock:
    """Mock ChromaDB client."""
    chroma_mock = MagicMock()
    chroma_mock.add_documents = AsyncMock(return_value=["doc1"])
    chroma_mock.query = AsyncMock(return_value={
        "documents": [["Related content 1", "Related content 2"]],
        "metadatas": [[{"source": "note1"}, {"source": "note2"}]],
        "distances": [[0.1, 0.2]]
    })
    return chroma_mock


@pytest.fixture
def test_user_data(valid_email, valid_password, valid_full_name) -> dict:
    """Generate secure user data for testing.
    
    Uses random data to avoid leaking sensitive patterns.
    """
    return {
        "email": valid_email,
        "username": test_data.random_username(),
        "password": valid_password,
        "full_name": valid_full_name,
    }


@pytest.fixture
def test_note_data() -> dict:
    """Sample note data for testing."""
    return {
        "title": "Test Note",
        "content": "This is test content for a note",
        "subject": "Mathematics",
        "tags": ["algebra", "equations"]
    }


@pytest.fixture
def test_quiz_data() -> dict:
    """Sample quiz data for testing."""
    return {
        "title": "Math Quiz",
        "subject": "Mathematics",
        "question_count": 5,
        "difficulty": "medium"
    }


@pytest.fixture
def auth_headers(client: AsyncClient, test_user_data: dict) -> dict:
    """
    Create authenticated user and return auth headers.
    
    Returns headers with JWT token for authenticated requests.
    """
    async def _create_and_auth():
        # Register user
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    return _create_and_auth


@pytest.fixture
def temp_upload_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for file uploads during testing.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image_file(temp_upload_dir: Path) -> Path:
    """
    Create a sample image file for testing OCR upload.
    """
    import base64
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='white')
    img_path = temp_upload_dir / "test_image.png"
    img.save(img_path)
    
    return img_path


# Test markers configuration
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, may use external services)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full workflow)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "auth: Authentication related tests"
    )
    config.addinivalue_line(
        "markers", "api: API endpoint tests"
    )
    config.addinivalue_line(
        "markers", "ocr: OCR related tests"
    )
    config.addinivalue_line(
        "markers", "ai: AI/LLM related tests"
    )
