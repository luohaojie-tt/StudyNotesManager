"""
Integration tests for mindmap API endpoints.
"""
import uuid

import pytest
from httpx import AsyncClient

# Import fixtures needed
from tests.fixtures.test_data import test_data


@pytest.mark.integration
@pytest.mark.api
class TestMindmapAPI:
    """Test mindmap API endpoints."""

    @pytest.mark.asyncio
    async def test_generate_mindmap_requires_auth(self, client: AsyncClient):
        """Test that mindmap generation requires authentication."""
        response = await client.post(f"/api/mindmaps/generate/{uuid.uuid4()}")

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_mindmap_by_note_requires_auth(self, client: AsyncClient):
        """Test that getting mindmap by note requires authentication."""
        response = await client.get(f"/api/mindmaps/note/{uuid.uuid4()}")

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_mindmap_by_id_requires_auth(self, client: AsyncClient):
        """Test that getting mindmap by ID requires authentication."""
        response = await client.get(f"/api/mindmaps/{uuid.uuid4()}")

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_delete_mindmap_requires_auth(self, client: AsyncClient):
        """Test that deleting mindmap requires authentication."""
        response = await client.delete(f"/api/mindmaps/{uuid.uuid4()}")

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_update_mindmap_requires_auth(self, client: AsyncClient):
        """Test that updating mindmap requires authentication."""
        response = await client.put(
            f"/api/mindmaps/{uuid.uuid4()}", json={"id": "root", "text": "Test", "children": []}
        )

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_mindmap_versions_requires_auth(self, client: AsyncClient):
        """Test that getting mindmap versions requires authentication."""
        response = await client.get(f"/api/mindmaps/{uuid.uuid4()}/versions")

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_get_knowledge_points_requires_auth(self, client: AsyncClient):
        """Test that getting knowledge points requires authentication."""
        response = await client.get(f"/api/mindmaps/{uuid.uuid4()}/knowledge-points")

        # Should return 401 or 403 (CSRF)
        assert response.status_code in [401, 403]
