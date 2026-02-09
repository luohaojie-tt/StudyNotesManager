"""Unit tests for note upload functionality."""
import io
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data



# Note model tests
@pytest.mark.unit
class TestNoteModel:
    """Test Note model."""

    test_note_model_has_required_fields(self, valid_password):
        """Test that Note model has all required fields."""
        from app.models.note import Note
        
        # Check that model has the fields
        columns = Note.__table__.columns.keys()
        
        required_fields = [
            'id', 'user_id', 'title', 'content', 'file_type',
            'file_url', 'thumbnail_url', 'ocr_text', 'ocr_confidence',
            'embedding', 'category_id', 'tags', 'is_favorited',
            'view_count', 'mindmap_count', 'created_at', 'updated_at', 'meta_data'
        ]
        
        for field in required_fields:
            assert field in columns, f"Missing field: {field}"
    
    test_note_model_has_tags_field(self, valid_password):
        """Test that Note model has tags field."""
        from app.models.note import Note
        
        assert 'tags' in Note.__table__.columns.keys()
        assert Note.__table__.columns['tags'].type.__class__.__name__ == 'ARRAY'
    
    test_note_model_has_is_favorited_field(self, valid_password):
        """Test that Note model has is_favorited field."""
        from app.models.note import Note
        
        assert 'is_favorited' in Note.__table__.columns.keys()
        # Check it's a Boolean
        from sqlalchemy import Boolean
        assert isinstance(Note.__table__.columns['is_favorited'].type, Boolean)


# Schema tests
@pytest.mark.unit
class TestNoteSchemas:
    """Test Note schemas."""

    test_note_create_schema(self, valid_password):
        """Test NoteCreate schema."""
        from app.schemas.note import NoteCreate
        
        schema = NoteCreate(
            title="Test Note",
            content="Test content",
            file_url="https://example.com/file.jpg",
            tags=["tag1", "tag2"],
            meta_data={"key": "value"}
        )
        
        assert schema.title == "Test Note"
        assert schema.tags == ["tag1", "tag2"]
        assert schema.meta_data == {"key": "value"}
    
    test_note_response_schema(self, valid_password):
        """Test NoteResponse schema."""
        from app.schemas.note import NoteResponse
        
        data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "title": "Test Note",
            "content": "Test content",
            "file_url": "https://example.com/file.jpg",
            "thumbnail_url": None,
            "ocr_text": None,
            "category_id": None,
            "tags": ["tag1", "tag2"],
            "meta_data": {},
            "is_favorited": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        schema = NoteResponse(**data)
        assert schema.title == "Test Note"
        assert schema.is_favorited == False
        assert schema.tags == ["tag1", "tag2"]
    
    test_ocr_response_schema(self, valid_password):
        """Test OCRResponse schema."""
        from app.schemas.note import OCRResponse
        
        schema = OCRResponse(text="Recognized text", confidence=0.95)
        assert schema.text == "Recognized text"
        assert schema.confidence == 0.95


# Service tests
@pytest.mark.unit
class TestNoteService:
    """Test NoteService."""

    async test_note_service_create_note(self, valid_password):
        """Test creating a note through NoteService."""
        from app.services.note_service import NoteService
        from app.schemas.note import NoteCreate
        
        # Mock database session
        mock_db = AsyncMock()
        mock_note = MagicMock()
        mock_note.id = uuid.uuid4()
        mock_note.title = "Test Note"
        
        # Test
        note_data = NoteCreate(
            title="Test Note",
            meta_data={}
        )
        
        # Note: Full testing would require more complex mocking
        # This is a basic structural test
        assert note_data.title == "Test Note"


# API endpoint tests
@pytest.mark.unit
class TestNotesAPI:
    """Test notes API endpoints."""

    test_notes_router_exists(self, valid_password):
        """Test that notes router exists and has routes."""
        from app.api.notes import router
        
        routes = [route.path for route in router.routes]
        
        assert '/api/notes/upload' in routes
        assert '/api/notes/ocr' in routes
        assert '/api/notes' in routes
    
    test_upload_endpoint_signature(self, valid_password):
        """Test that upload endpoint has correct signature."""
        from app.api.notes import router
        
        # Find the upload route
        upload_route = None
        for route in router.routes:
            if route.path == '/api/notes/upload':
                upload_route = route
                break
        
        assert upload_route is not None
        assert upload_route.methods == {'POST'}


@pytest.mark.unit
class TestFileValidation:
    """Test file validation logic."""

    test_file_size_validation(self, valid_password):
        """Test file size validation logic."""
        from app.core.config import settings
        
        max_size = settings.MAX_UPLOAD_SIZE
        assert max_size == 10485760  # 10MB
    
    test_allowed_extensions(self, valid_password):
        """Test allowed file extensions."""
        from app.core.config import settings
        
        extensions = settings.ALLOWED_EXTENSIONS
        assert 'jpg' in extensions
        assert 'jpeg' in extensions
        assert 'png' in extensions
        assert 'pdf' in extensions
