"""
Unit tests for mindmap generation functionality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data



@pytest.mark.unit
@pytest.mark.ai
class TestMindmapService:
    """Test mindmap generation service."""

    @pytest.fixture
    def mock_deepseek_client(self):
        """Mock DeepSeek API client."""
        client = AsyncMock()
        client.chat.return_value = {
            "choices": [
                {
                    "message": {
                        "content": """
                        {
                            "nodes": [
                                {"id": "root", "label": "Main Topic", "level": 0},
                                {"id": "c1", "label": "Concept 1", "level": 1},
                                {"id": "c2", "label": "Concept 2", "level": 1}
                            ],
                            "edges": [
                                {"from": "root", "to": "c1"},
                                {"from": "root", "to": "c2"}
                            ]
                        }
                        """
                    }
                }
            ]
        }
        return client

    @pytest.mark.asyncio
    async def test_generate_mindmap_from_text(self, mock_deepseek_client):
        """Test generating mindmap from text content."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        text_content = """
        Mathematics is the study of numbers, shapes, and patterns.
        It includes algebra, calculus, and geometry.
        """

        mindmap = await service.generate_mindmap(text_content)

        assert "nodes" in mindmap
        assert "edges" in mindmap
        assert len(mindmap["nodes"]) > 0
        assert len(mindmap["edges"]) > 0

    @pytest.mark.asyncio
    async def test_mindmap_has_root_node(self, mock_deepseek_client):
        """Test that mindmap has a root node."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        text_content = "Test content about a topic"

        mindmap = await service.generate_mindmap(text_content)

        # Should have at least one node with level 0 (root)
        root_nodes = [n for n in mindmap["nodes"] if n.get("level") == 0]
        assert len(root_nodes) > 0

    @pytest.mark.asyncio
    async def test_mindmap_nodes_have_required_fields(self, mock_deepseek_client):
        """Test that mindmap nodes have required fields."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        text_content = "Test content"

        mindmap = await service.generate_mindmap(text_content)

        for node in mindmap["nodes"]:
            assert "id" in node
            assert "label" in node
            assert "level" in node

    @pytest.mark.asyncio
    async def test_mindmap_edges_valid_structure(self, mock_deepseek_client):
        """Test that mindmap edges have valid structure."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        text_content = "Test content with multiple concepts"

        mindmap = await service.generate_mindmap(text_content)

        node_ids = {n["id"] for n in mindmap["nodes"]}

        for edge in mindmap["edges"]:
            assert "from" in edge
            assert "to" in edge
            # Edge endpoints should reference existing nodes
            assert edge["from"] in node_ids
            assert edge["to"] in node_ids

    @pytest.mark.asyncio
    async def test_mindmap_from_note(self, mock_deepseek_client):
        """Test generating mindmap from a note object."""
        from app.services.mindmap_service import MindmapService
        from app.models.note import Note
        from datetime import datetime

        service = MindmapService(mock_deepseek_client)

        note = Note(
            id=1,
            title="Mathematics Basics",
            content="Algebra and calculus are key areas",
            subject="Mathematics",
            owner_id=1,
            created_at=datetime.now()
        )

        mindmap = await service.generate_mindmap_from_note(note)

        assert "nodes" in mindmap
        assert "edges" in mindmap
        # Root node should reflect note title
        root_nodes = [n for n in mindmap["nodes"] if n.get("level") == 0]
        assert len(root_nodes) > 0

    @pytest.mark.asyncio
    async def test_mindmap_error_handling(self, mock_deepseek_client):
        """Test error handling in mindmap generation."""
        from app.services.mindmap_service import MindmapService

        # Mock API error
        mock_deepseek_client.chat.side_effect = Exception("API Error")

        service = MindmapService(mock_deepseek_client)

        with pytest.raises(Exception):
            await service.generate_mindmap("Test content")

    @pytest.mark.asyncio
    async def test_mindmap_caching(self, mock_deepseek_client):
        """Test that mindmap generation uses caching."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        text_content = "Test content for caching"

        # First call
        mindmap1 = await service.generate_mindmap(text_content)

        # Second call should use cache
        mindmap2 = await service.generate_mindmap(text_content)

        # Should return same result
        assert mindmap1 == mindmap2

    @pytest.mark.asyncio
    async def test_mindmap_different_content_different_result(self, mock_deepseek_client):
        """Test that different content produces different mindmaps."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        mindmap1 = await service.generate_mindmap("Content about mathematics")
        mindmap2 = await service.generate_mindmap("Content about history")

        # Should be different
        assert mindmap1 != mindmap2


@pytest.mark.unit
@pytest.mark.ai
class TestMindmapFormatting:
    """Test mindmap data formatting and validation."""

    test_validate_mindmap_structure(self, valid_password):
        """Test mindmap structure validation."""
        from app.services.mindmap_service import MindmapService

        valid_mindmap = {
            "nodes": [
                {"id": "root", "label": "Main", "level": 0},
                {"id": "c1", "label": "Child 1", "level": 1}
            ],
            "edges": [
                {"from": "root", "to": "c1"}
            ]
        }

        service = MindmapService(None)
        assert service.validate_mindmap(valid_mindmap) is True

    test_validate_mindmap_missing_nodes(self, valid_password):
        """Test validation fails when nodes are missing."""
        from app.services.mindmap_service import MindmapService

        invalid_mindmap = {
            "nodes": [],
            "edges": []
        }

        service = MindmapService(None)
        assert service.validate_mindmap(invalid_mindmap) is False

    test_validate_mindmap_orphaned_edges(self, valid_password):
        """Test validation fails with orphaned edges."""
        from app.services.mindmap_service import MindmapService

        invalid_mindmap = {
            "nodes": [
                {"id": "root", "label": "Main", "level": 0}
            ],
            "edges": [
                {"from": "nonexistent", "to": "also_nonexistent"}
            ]
        }

        service = MindmapService(None)
        assert service.validate_mindmap(invalid_mindmap) is False

    test_format_mindmap_for_frontend(self, valid_password):
        """Test formatting mindmap for frontend consumption."""
        from app.services.mindmap_service import MindmapService

        mindmap = {
            "nodes": [
                {"id": "root", "label": "Main", "level": 0},
                {"id": "c1", "label": "Child 1", "level": 1}
            ],
            "edges": [
                {"from": "root", "to": "c1"}
            ]
        }

        service = MindmapService(None)
        formatted = service.format_for_frontend(mindmap)

        assert "graph" in formatted
        assert "nodes" in formatted["graph"]
        assert "links" in formatted["graph"]


@pytest.mark.unit
@pytest.mark.ai
class TestMindmapOptimization:
    """Test mindmap generation optimizations."""

    @pytest.mark.asyncio
    async def test_mindmap_depth_limit(self, mock_deepseek_client):
        """Test that mindmap depth is limited."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        long_content = "Very long content " * 100
        mindmap = await service.generate_mindmap(long_content)

        # Check max depth
        max_level = max(n.get("level", 0) for n in mindmap["nodes"])
        assert max_level <= 5  # Should not exceed 5 levels

    @pytest.mark.asyncio
    async def test_mindmap_node_count_limit(self, mock_deepseek_client):
        """Test that mindmap node count is reasonable."""
        from app.services.mindmap_service import MindmapService

        service = MindmapService(mock_deepseek_client)

        long_content = "Very detailed content " * 100
        mindmap = await service.generate_mindmap(long_content)

        # Should have reasonable number of nodes (< 50)
        assert len(mindmap["nodes"]) <= 50
