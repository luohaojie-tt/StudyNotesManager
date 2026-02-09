"""
Unit tests for DeepSeekService.
"""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import httpx


@pytest.mark.unit
class TestDeepSeekService:
    """Test DeepSeekService methods."""

    @pytest.fixture
    def mock_client(self):
        """Create mock HTTP client."""
        client = MagicMock()
        client.post = AsyncMock()
        client.aclose = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_generate_completion_success(self, mock_client):
        """Test successful text completion generation."""
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Generated text response"
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.post.return_value = mock_response

        with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()
            service.client = mock_client

            # Act
            result = await service.generate_completion(
                prompt="Test prompt",
                max_tokens=100
            )

            # Assert
            assert result == "Generated text response"
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_mindmap_success(self, mock_client):
        """Test successful mindmap generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"id": "root", "text": "Mathematics", "children": []}'
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.post.return_value = mock_response

        with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()
            service.client = mock_client

            result = await service.generate_mindmap(
                note_content="Algebra content",
                note_title="Algebra",
                max_levels=3
            )

            assert "id" in result
            assert result["text"] == "Mathematics"

    @pytest.mark.asyncio
    async def test_generate_quiz_questions_success(self, mock_client):
        """Test successful quiz question generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"questions": [{"id": "q1", "question_text": "What is 2+2?", "options": ["3", "4", "5"], "correct_answer": "4"}]}'
                    }
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.post.return_value = mock_response

        with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()
            service.client = mock_client

            result = await service.generate_quiz_questions(
                knowledge_points=["Algebra basics"],
                question_count=5,
                difficulty="medium"
            )

            assert "questions" in result

    @pytest.mark.asyncio
    async def test_make_request_with_retry(self, mock_client):
        """Test API request with retry on rate limit."""
        # First call fails with 429, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 429
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Rate limit", request=MagicMock(), response=mock_response_fail
        )

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"result": "success"}
        mock_response_success.raise_for_status = MagicMock()

        mock_client.post.side_effect = [
            mock_response_fail,
            mock_response_success
        ]

        with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()
            service.client = mock_client

            result = await service._make_request("/test", {"data": "test"}, max_retries=2)

            assert result == {"result": "success"}
            assert mock_client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_error_rate_limit(self, mock_client):
        """Test rate limit error handling."""
        with patch('app.services.deepseek_service.asyncio.sleep', new_callable=AsyncMock):
            with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
                from app.services.deepseek_service import DeepSeekService

                service = DeepSeekService()

                # Should not raise, just sleep
                await service._handle_error(429)

    @pytest.mark.asyncio
    async def test_handle_error_server_error(self, mock_client):
        """Test server error handling."""
        with patch('app.services.deepseek_service.asyncio.sleep', new_callable=AsyncMock):
            with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
                from app.services.deepseek_service import DeepSeekService

                service = DeepSeekService()

                # Should not raise, just sleep
                await service._handle_error(500)

    @pytest.mark.asyncio
    async def test_close_service(self, mock_client):
        """Test closing service connections."""
        with patch('app.services.deepseek_service.httpx.AsyncClient', return_value=mock_client):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()
            service.client = mock_client

            await service.close()

            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_mindmap_structure_valid(self):
        """Test validation of valid mindmap structure."""
        with patch('app.services.deepseek_service.httpx.AsyncClient'):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()

            valid_structure = {
                "id": "root",
                "text": "Mathematics",
                "children": [
                    {
                        "id": "algebra",
                        "text": "Algebra",
                        "children": []
                    }
                ]
            }

            # Should not raise
            service._validate_mindmap_structure(valid_structure, max_levels=3)

    @pytest.mark.asyncio
    async def test_validate_mindmap_structure_invalid_depth(self):
        """Test validation fails for too deep structure."""
        with patch('app.services.deepseek_service.httpx.AsyncClient'):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()

        # Create deep structure
        deep_structure = {"id": "root", "text": "Root", "children": []}
        current = deep_structure
        for i in range(10):  # More than max_levels
            new_child = {"id": f"node_{i}", "text": f"Node {i}", "children": []}
            current["children"] = [new_child]
            current = new_child

        # Should raise ValueError
        with pytest.raises(ValueError, match="too deep"):
            service._validate_mindmap_structure(deep_structure, max_levels=3)

    @pytest.mark.asyncio
    async def test_validate_mindmap_structure_missing_fields(self):
        """Test validation fails for missing required fields."""
        with patch('app.services.deepseek_service.httpx.AsyncClient'):
            from app.services.deepseek_service import DeepSeekService

            service = DeepSeekService()

        invalid_structure = {
            "id": "root"
            # Missing "text" field
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="missing required fields"):
            service._validate_mindmap_structure(invalid_structure, max_levels=3)
