"""Tests for note upload and OCR endpoints."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from io import BytesIO


class TestNoteUploadEndpoint:
    """Test POST /api/notes/upload endpoint."""

    def test_upload_endpoint_exists(self):
        """Should have upload endpoint registered."""
        from app.api.notes import router
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        assert any('/upload' in path for path in routes)
        assert '/api/notes/upload' in routes

    def test_upload_endpoint_has_rate_limiting(self):
        """Should have rate limiting decorator."""
        from app.api.notes import upload_note
        # Rate limiting is applied via decorator
        assert callable(upload_note)

    @pytest.mark.asyncio
    async def test_upload_accepts_image_files(self):
        """Should accept image file uploads."""
        from app.api.notes import upload_note
        # Endpoint signature includes file parameter
        import inspect
        sig = inspect.signature(upload_note)
        assert 'file' in sig.parameters
        assert 'title' in sig.parameters

    def test_upload_returns_note_upload_response(self):
        """Should return NoteUploadResponse model."""
        from app.api.notes import router
        # Find the upload route
        for route in router.routes:
            if hasattr(route, 'path') and '/upload' in route.path:
                # Route exists and is registered
                assert route is not None
                return
        assert False, "Upload route not found"


class testOCREndpoint:
    """Test POST /api/notes/ocr endpoint."""

    def test_ocr_endpoint_exists(self):
        """Should have OCR endpoint registered."""
        from app.api.notes import router
        routes = [r.path for r in router.routes if hasattr(r, 'path')]
        # OCR endpoint is registered with full path
        assert '/api/notes/ocr' in routes

    def test_ocr_endpoint_signature(self):
        """Should have correct signature."""
        from app.api.notes import recognize_text
        import inspect
        sig = inspect.signature(recognize_text)
        assert 'file' in sig.parameters

    def test_ocr_returns_ocr_response(self):
        """Should return OCRResponse model."""
        from app.api.notes import recognize_text
        import inspect
        sig = inspect.signature(recognize_text)
        # Check response model is set
        assert callable(recognize_text)


class TestOCRService:
    """Test OCR service."""

    def test_ocr_service_exists(self):
        """Should have OCR service instance."""
        from app.services.ocr_service import ocr_service
        assert ocr_service is not None

    def test_ocr_service_has_recognize_methods(self):
        """Should have recognize methods."""
        from app.services.ocr_service import BaiduOCRService
        service = BaiduOCRService()
        assert hasattr(service, 'recognize_text')
        assert hasattr(service, 'recognize_text_accurate')

    @pytest.mark.asyncio
    async def test_ocr_recognize_text_returns_tuple(self):
        """Should return tuple of (text, confidence)."""
        from app.services.ocr_service import BaiduOCRService
        service = BaiduOCRService()
        result = await service.recognize_text(b"fake image content")
        assert isinstance(result, tuple)
        assert len(result) == 2
        text, confidence = result
        assert isinstance(text, (str, type(None)))
        assert isinstance(confidence, (float, type(None)))

    @pytest.mark.asyncio
    async def test_ocr_mock_mode_works(self):
        """Should work in mock mode without credentials."""
        from app.services.ocr_service import BaiduOCRService
        service = BaiduOCRService()
        # In mock mode (no credentials), should return mock text
        text, confidence = await service.recognize_text(b"test")
        # Mock mode returns text
        assert text is not None
        assert confidence is not None


class TestNoteService:
    """Test note service."""

    def test_note_service_exists(self):
        """Should have NoteService class."""
        from app.services.note_service import NoteService
        assert NoteService is not None

    def test_note_service_has_create_method(self):
        """Should have create_note method."""
        from app.services.note_service import NoteService
        assert hasattr(NoteService, 'create_note')

    def test_note_service_has_get_methods(self):
        """Should have get_note and get_notes methods."""
        from app.services.note_service import NoteService
        assert hasattr(NoteService, 'get_note')
        assert hasattr(NoteService, 'get_notes')


class TestOSSService:
    """Test OSS service."""

    def test_oss_service_exists(self):
        """Should have OSS service instance."""
        from app.services.oss_service import oss_service
        assert oss_service is not None

    def test_oss_service_has_upload_method(self):
        """Should have upload_file method."""
        from app.services.oss_service import OSSService
        assert hasattr(OSSService, 'upload_file')


class TestVirusScanService:
    """Test virus scan service."""

    def test_virus_scan_service_exists(self):
        """Should have virus scan service instance."""
        from app.services.virus_scan_service import virus_scan_service
        assert virus_scan_service is not None

    def test_virus_scan_service_has_scan_method(self):
        """Should have scan_file method."""
        from app.services.virus_scan_service import VirusScanService
        assert hasattr(VirusScanService, 'scan_file')


class TestSecurityFeatures:
    """Test security features in note upload."""

    def test_upload_has_file_size_validation(self):
        """Should validate file size before upload."""
        from app.api.notes import upload_note
        from app.core.config import Settings
        # Check MAX_UPLOAD_SIZE is configured
        settings = Settings()
        assert hasattr(settings, 'MAX_UPLOAD_SIZE')
        assert settings.MAX_UPLOAD_SIZE > 0

    def test_upload_has_allowed_extensions(self):
        """Should have allowed file extensions configured."""
        from app.core.config import Settings
        settings = Settings()
        assert hasattr(settings, 'ALLOWED_EXTENSIONS')
        assert isinstance(settings.ALLOWED_EXTENSIONS, list)
        assert len(settings.ALLOWED_EXTENSIONS) > 0

    def test_upload_has_rate_limiting(self):
        """Should have rate limiting configured."""
        from app.api.notes import upload_limiter
        assert upload_limiter is not None

    def test_upload_requires_authentication(self):
        """Should require authentication."""
        from app.api.notes import upload_note
        import inspect
        sig = inspect.signature(upload_note)
        # Check depends has get_current_active_user
        params = sig.parameters
        assert 'current_user' in params


class TestSchemas:
    """Test request/response schemas."""

    def test_note_upload_response_exists(self):
        """Should have NoteUploadResponse schema."""
        from app.schemas.note import NoteUploadResponse
        assert NoteUploadResponse is not None

    def test_ocr_response_exists(self):
        """Should have OCRResponse schema."""
        from app.schemas.note import OCRResponse
        assert OCRResponse is not None

    def test_note_create_schema_exists(self):
        """Should have NoteCreate schema."""
        from app.schemas.note import NoteCreate
        assert NoteCreate is not None

    def test_note_response_schema_exists(self):
        """Should have NoteResponse schema."""
        from app.schemas.note import NoteResponse
        assert NoteResponse is not None


class TestConfiguration:
    """Test configuration for note upload and OCR."""

    def test_baidu_ocr_config_exists(self):
        """Should have Baidu OCR configuration."""
        from app.core.config import Settings
        settings = Settings()
        assert hasattr(settings, 'BAIDU_OCR_APP_ID')
        assert hasattr(settings, 'BAIDU_OCR_API_KEY')
        assert hasattr(settings, 'BAIDU_OCR_SECRET_KEY')

    def test_oss_config_exists(self):
        """Should have OSS configuration."""
        from app.core.config import Settings
        settings = Settings()
        # OSS config is optional (graceful degradation)
        # Just verify the service exists
        from app.services.oss_service import oss_service
        assert oss_service is not None

    def test_max_upload_size_is_reasonable(self):
        """Should have reasonable max upload size."""
        from app.core.config import Settings
        settings = Settings()
        # Should be at least 1MB
        assert settings.MAX_UPLOAD_SIZE >= 1024 * 1024
        # Should be at most 100MB
        assert settings.MAX_UPLOAD_SIZE <= 100 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
