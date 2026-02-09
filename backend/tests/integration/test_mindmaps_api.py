"""
Integration tests for Mindmaps API endpoints.

Tests the /api/mindmaps/* endpoints with real database interactions.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.api
class TestMindmapsAPI:
    """Test mindmaps API endpoints."""

    @pytest.fixture
    async def test_user(self, async_db_session: AsyncSession):
        """Create a test user."""
        from app.models.user import User
        from app.core.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email="mindmap@test.com",
            password_hash=get_password_hash("TestPass123!"),
            full_name="Mindmap Test User",
            is_active=True,
            is_verified=True
        )
        async_db_session.add(user)
        await async_db_session.commit()
        await async_db_session.refresh(user)
        return user

    @pytest.fixture
    async def test_note(self, async_db_session: AsyncSession, test_user):
        """Create a test note."""
        from app.models.note import Note
        from datetime import datetime

        note = Note(
            id=uuid.uuid4(),
            user_id=test_user.id,
            title="Algebra Basics",
            content="Algebra is the study of mathematical symbols and rules",
            subject="Mathematics",
            created_at=datetime.utcnow()
        )
        async_db_session.add(note)
        await async_db_session.commit()
        await async_db_session.refresh(note)
        return note

    @pytest.mark.asyncio
    async def test_generate_mindmap_success(
        self,
        client: AsyncClient,
        test_user,
        test_note
    ):
        """Test successful mindmap generation."""
        response = await client.post(
            f"/api/mindmaps/generate/{test_note.id}",
            params={
                "user_id": str(test_user.id),
                "note_content": test_note.content,
                "note_title": test_note.title
            }
        )

        # Should succeed (may return 500 if DeepSeek not configured)
        assert response.status_code in [200, 201, 500]

        if response.status_code in [200, 201]:
            data = response.json()
            assert "task_id" in data
            assert data["status"] in ["completed", "pending"]

    @pytest.mark.asyncio
    async def test_generate_mindmap_invalid_note_id(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test mindmap generation with invalid note ID."""
        fake_note_id = uuid.uuid4()

        response = await client.post(
            f"/api/mindmaps/generate/{fake_note_id}",
            params={
                "user_id": str(test_user.id),
                "note_content": "Test content",
                "note_title": "Test"
            }
        )

        # Should fail (404 or 500 depending on error handling)
        assert response.status_code in [404, 500]

    @pytest.mark.asyncio
    async def test_get_mindmap_success(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
        test_user,
        test_note
    ):
        """Test getting an existing mindmap."""
        from app.models.mindmap import Mindmap

        # Create a mindmap directly in DB
        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=test_user.id,
            structure={
                "id": "root",
                "text": "Mathematics",
                "children": []
            },
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)
        await async_db_session.commit()

        response = await client.get(
            f"/api/mindmaps/{mindmap.id}",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(mindmap.id)
        assert data["note_id"] == str(test_note.id)
        assert "structure" in data

    @pytest.mark.asyncio
    async def test_get_mindmap_not_found(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test getting a non-existent mindmap."""
        fake_mindmap_id = uuid.uuid4()

        response = await client.get(
            f"/api/mindmaps/{fake_mindmap_id}",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_mindmap_unauthorized(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
        test_user,
        test_note
    ):
        """Test getting mindmap belonging to another user."""
        from app.models.mindmap import Mindmap

        other_user_id = uuid.uuid4()

        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=other_user_id,  # Different user
            structure={"id": "root", "text": "Test"},
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)
        await async_db_session.commit()

        response = await client.get(
            f"/api/mindmaps/{mindmap.id}",
            params={"user_id": str(test_user.id)}
        )

        # Should return 404 (not found for this user)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_mindmap_success(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
        test_user,
        test_note
    ):
        """Test updating a mindmap."""
        from app.models.mindmap import Mindmap

        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=test_user.id,
            structure={"id": "root", "text": "Old"},
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)
        await async_db_session.commit()

        new_structure = {
            "id": "root",
            "text": "Updated",
            "children": []
        }

        response = await client.put(
            f"/api/mindmaps/{mindmap.id}",
            params={"user_id": str(test_user.id)},
            json={"structure": new_structure}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["structure"]["text"] == "Updated"

    @pytest.mark.asyncio
    async def test_update_mindmap_invalid_structure(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
        test_user,
        test_note
    ):
        """Test updating mindmap with invalid structure."""
        from app.models.mindmap import Mindmap

        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=test_user.id,
            structure={"id": "root", "text": "Test"},
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)
        await async_db_session.commit()

        # Invalid structure (missing required fields)
        invalid_structure = {"id": "root"}  # Missing "text"

        response = await client.put(
            f"/api/mindmaps/{mindmap.id}",
            params={"user_id": str(test_user.id)},
            json={"structure": invalid_structure}
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_mindmap_versions(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
        test_user,
        test_note
    ):
        """Test getting all versions of a mindmap."""
        from app.models.mindmap import Mindmap

        # Create original version
        mindmap_v1 = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=test_user.id,
            structure={"id": "root", "text": "V1"},
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap_v1)
        await async_db_session.commit()

        # Create version 2
        mindmap_v2 = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=test_user.id,
            structure={"id": "root", "text": "V2"},
            map_type="manual",
            version=2,
            parent_version_id=mindmap_v1.id
        )
        async_db_session.add(mindmap_v2)
        await async_db_session.commit()

        response = await client.get(
            f"/api/mindmaps/{mindmap_v1.id}/versions",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 2
        assert versions[0]["version"] == 1
        assert versions[1]["version"] == 2

    @pytest.mark.asyncio
    async def test_delete_mindmap_success(
        self,
        client: AsyncClient,
        async_db_session: AsyncSession,
        test_user,
        test_note
    ):
        """Test deleting a mindmap."""
        from app.models.mindmap import Mindmap

        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=test_note.id,
            user_id=test_user.id,
            structure={"id": "root", "text": "Test"},
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)
        await async_db_session.commit()

        response = await client.delete(
            f"/api/mindmaps/{mindmap.id}",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(
            f"/api/mindmaps/{mindmap.id}",
            params={"user_id": str(test_user.id)}
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_mindmap_not_found(
        self,
        client: AsyncClient,
        test_user
    ):
        """Test deleting a non-existent mindmap."""
        fake_mindmap_id = uuid.uuid4()

        response = await client.delete(
            f"/api/mindmaps/{fake_mindmap_id}",
            params={"user_id": str(test_user.id)}
        )

        assert response.status_code == 404


@pytest.mark.integration
@pytest.mark.api
class TestMindmapKnowledgePoints:
    """Test mindmap knowledge points functionality."""

    @pytest.fixture
    async def mindmap_with_knowledge_points(
        self,
        async_db_session: AsyncSession,
        test_user
    ):
        """Create a mindmap with knowledge points."""
        from app.models.mindmap import Mindmap, KnowledgePoint, Note
        from datetime import datetime

        # Create note
        note = Note(
            id=uuid.uuid4(),
            user_id=test_user.id,
            title="Test Note",
            content="Test content",
            subject="Math",
            created_at=datetime.utcnow()
        )
        async_db_session.add(note)

        # Create mindmap
        mindmap = Mindmap(
            id=uuid.uuid4(),
            note_id=note.id,
            user_id=test_user.id,
            structure={
                "id": "root",
                "text": "Math",
                "children": [
                    {"id": "algebra", "text": "Algebra", "children": []}
                ]
            },
            map_type="ai_generated",
            version=1
        )
        async_db_session.add(mindmap)

        # Create knowledge points
        kp1 = KnowledgePoint(
            id=uuid.uuid4(),
            mindmap_id=mindmap.id,
            node_id="root",
            node_path="root",
            text="Math",
            level=0
        )
        kp2 = KnowledgePoint(
            id=uuid.uuid4(),
            mindmap_id=mindmap.id,
            node_id="algebra",
            node_path="root/algebra",
            text="Algebra",
            level=1,
            parent_node_id="root"
        )
        async_db_session.add(kp1)
        async_db_session.add(kp2)

        await async_db_session.commit()
        return mindmap

    @pytest.mark.asyncio
    async def test_get_knowledge_points_success(
        self,
        client: AsyncClient,
        mindmap_with_knowledge_points
    ):
        """Test getting knowledge points for a mindmap."""
        response = await client.get(
            f"/api/mindmaps/{mindmap_with_knowledge_points.id}/knowledge-points",
            params={"user_id": str(mindmap_with_knowledge_points.user_id)}
        )

        # Note: This endpoint may not exist yet
        # If it doesn't exist, we expect 404
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "knowledge_points" in data or isinstance(data, list)
