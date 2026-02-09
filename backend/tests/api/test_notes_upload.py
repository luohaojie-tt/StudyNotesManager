"""
Notes upload API integration tests.
"""
import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient):
    """Create authenticated user and return auth headers."""
    # Register user
    await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "SecurePass123",
            "full_name": "Test User"
        }
    )
    
    # Login
    response = await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "SecurePass123"
        }
    )
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_note_id(client: AsyncClient, auth_headers: dict):
    """Create a test note and return its ID."""
    with patch("app.api.notes.oss_service.upload_file", new_callable=AsyncMock) as mock_upload, \
         patch("app.api.notes.ocr_service.recognize_text_accurate", new_callable=AsyncMock) as mock_ocr:
        mock_upload.return_value = "https://oss.example.com/notes/test.jpg"
        mock_ocr.return_value = ("Recognized text", 0.95)
        
        response = await client.post(
            "/api/notes/upload",
            headers=auth_headers,
            data={"title": "Test Note", "category_id": None, "tags": None},
            files={"file": ("test.jpg", io.BytesIO(b"content"), "image/jpeg")}
        )
        
        return response.json()["note"]["id"]


@pytest.mark.integration
@pytest.mark.notes
class TestNoteUploadEndpoint:
    """Test note upload endpoint."""

    async def test_upload_image_with_ocr_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test successful image upload with OCR recognition."""
        # Create a mock image file
        image_content = b"fake_image_content"

        with patch(
            "app.api.notes.oss_service.upload_file", new_callable=AsyncMock
        ) as mock_upload, patch(
            "app.api.notes.ocr_service.recognize_text_accurate",
            new_callable=AsyncMock,
        ) as mock_ocr:
            # Mock OSS upload
            mock_upload.return_value = "https://oss.example.com/notes/test.jpg"

            # Mock OCR recognition
            mock_ocr.return_value = ("Recognized text from image", 0.95)

            response = await client.post(
                "/api/notes/upload",
                headers=auth_headers,
                data={
                    "title": "Test Note",
                    "category_id": None,
                    "tags": "tag1,tag2",
                },
                files={"file": ("test.jpg", io.BytesIO(image_content), "image/jpeg")},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "note" in data
            assert "ocr_confidence" in data
            assert "file_size" in data
            assert "content_type" in data

            # Verify note data
            note = data["note"]
            assert note["title"] == "Test Note"
            assert note["file_url"] == "https://oss.example.com/notes/test.jpg"
            assert note["ocr_text"] == "Recognized text from image"
            assert data["ocr_confidence"] == 0.95
            assert data["file_size"] == len(image_content)
            assert data["content_type"] == "image/jpeg"

            # Verify mocks were called
            mock_upload.assert_called_once()
            mock_ocr.assert_called_once()

    async def test_upload_pdf_without_ocr(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test PDF upload (no OCR)."""
        pdf_content = b"fake_pdf_content"

        with patch(
            "app.api.notes.oss_service.upload_file", new_callable=AsyncMock
        ) as mock_upload:
            mock_upload.return_value = "https://oss.example.com/notes/test.pdf"

            response = await client.post(
                "/api/notes/upload",
                headers=auth_headers,
                data={
                    "title": "PDF Note",
                    "category_id": None,
                    "tags": None,
                },
                files={"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")},
            )

            assert response.status_code == 200
            data = response.json()

            note = data["note"]
            assert note["title"] == "PDF Note"
            assert note["file_url"] == "https://oss.example.com/notes/test.pdf"
            assert data["ocr_confidence"] is None
            assert data["content_type"] == "application/pdf"

    async def test_upload_file_too_large_returns_413(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test uploading file larger than limit returns 413."""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB

        response = await client.post(
            "/api/notes/upload",
            headers=auth_headers,
            data={"title": "Large File", "category_id": None, "tags": None},
            files={
                "file": (
                    "large.jpg",
                    io.BytesIO(large_content),
                    "image/jpeg",
                )
            },
        )

        # Should fail due to size limit
        assert response.status_code in [413, 500]

    async def test_upload_invalid_file_type_returns_400(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test uploading invalid file type returns error."""
        invalid_content = b"fake_content"

        response = await client.post(
            "/api/notes/upload",
            headers=auth_headers,
            data={"title": "Invalid File", "category_id": None, "tags": None},
            files={
                "file": ("test.exe", io.BytesIO(invalid_content), "application/exe")
            },
        )

        # Should fail due to invalid file type
        assert response.status_code in [400, 422]

    async def test_upload_missing_file_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test upload without file returns validation error."""
        response = await client.post(
            "/api/notes/upload",
            headers=auth_headers,
            data={"title": "No File", "category_id": None, "tags": None},
        )

        assert response.status_code == 422

    async def test_upload_missing_title_returns_422(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test upload without title returns validation error."""
        response = await client.post(
            "/api/notes/upload",
            headers=auth_headers,
            data={"category_id": None, "tags": None},
            files={"file": ("test.jpg", io.BytesIO(b"content"), "image/jpeg")},
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.notes
class TestNotesListEndpoint:
    """Test notes list endpoint."""

    async def test_get_notes_empty_list(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting notes when none exist."""
        response = await client.get("/api/notes", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "notes" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["notes"]) == 0

    async def test_get_notes_with_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting notes with pagination parameters."""
        response = await client.get(
            "/api/notes?skip=0&limit=10", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "page" in data
        assert "limit" in data
        assert data["page"] == 1
        assert data["limit"] == 10

    async def test_get_notes_with_search(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test searching notes."""
        response = await client.get(
            "/api/notes?search=test", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "notes" in data
        assert "total" in data


@pytest.mark.integration
@pytest.mark.notes
class TestNoteDetailEndpoint:
    """Test note detail endpoint."""

    async def test_get_note_by_id(
        self, client: AsyncClient, auth_headers: dict, test_note_id: str
    ):
        """Test getting a specific note by ID."""
        response = await client.get(f"/api/notes/{test_note_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert "title" in data
        assert data["id"] == test_note_id

    async def test_get_nonexistent_note_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting non-existent note returns 404."""
        response = await client.get(
            f"/api/notes/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.notes
class TestNoteDeleteEndpoint:
    """Test note deletion endpoint."""

    async def test_delete_note_success(
        self, client: AsyncClient, auth_headers: dict, test_note_id: str
    ):
        """Test successful note deletion."""
        response = await client.delete(
            f"/api/notes/{test_note_id}", headers=auth_headers
        )

        assert response.status_code == 204

    async def test_delete_nonexistent_note_returns_404(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent note returns 404."""
        response = await client.delete(
            f"/api/notes/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.notes
class TestNoteFavoriteEndpoint:
    """Test note favorite toggle endpoint."""

    async def test_toggle_favorite_success(
        self, client: AsyncClient, auth_headers: dict, test_note_id: str
    ):
        """Test toggling note favorite status."""
        response = await client.post(
            f"/api/notes/{test_note_id}/favorite", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert "is_favorited" in data
        assert isinstance(data["is_favorited"], bool)
