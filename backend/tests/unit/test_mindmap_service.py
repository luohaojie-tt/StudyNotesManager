"""
Unit tests for MindmapService.
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.mindmap_service import MindmapService
from app.models.mindmap import Mindmap, KnowledgePoint
from tests.fixtures.test_data import valid_password, valid_email, valid_full_name, test_data



@pytest.mark.unit
class TestMindmapService:
    """Test MindmapService methods."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.rollback = AsyncMock()
        db.execute = AsyncMock()
        db.delete = MagicMock()
        return db

    @pytest.fixture
    def mock_deepseek_service(self):
        """Create mock DeepSeek service."""
        service = MagicMock()
        service.generate_mindmap = AsyncMock(return_value={
            "id": "root",
            "text": "Mathematics",
            "children": [
                {
                    "id": "algebra",
                    "text": "Algebra",
                    "children": []
                }
            ]
        })
        service._validate_mindmap_structure = MagicMock()
        service.close = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_generate_mindmap_success(self, mock_db, mock_deepseek_service):
        """Test successful mindmap generation."""
        # Arrange
        note_id = uuid.uuid4()
        user_id = uuid.uuid4()
        note_content = "Algebra is the study of mathematical symbols"
        note_title = "Introduction to Algebra"

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db
            service.deepseek = mock_deepseek_service

            # Act
            result = await service.generate_mindmap(
                note_id=note_id,
                user_id=user_id,
                note_content=note_content,
                note_title=note_title
            )

            # Assert
            assert result is not None
            mock_db.add.assert_called()
            mock_db.flush.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_mindmap_calls_deepseek(self, mock_db, mock_deepseek_service):
        """Test that generate_mindmap calls DeepSeek service."""
        note_id = uuid.uuid4()
        user_id = uuid.uuid4()

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db
            service.deepseek = mock_deepseek_service

            await service.generate_mindmap(
                note_id=note_id,
                user_id=user_id,
                note_content="Test content",
                note_title="Test"
            )

            # Assert DeepSeek was called
            mock_deepseek_service.generate_mindmap.assert_called_once_with(
                note_content="Test content",
                note_title="Test",
                max_levels=5
            )

    @pytest.mark.asyncio
    async def test_get_mindmap_success(self, mock_db):
        """Test getting an existing mindmap."""
        # Arrange
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_mindmap = Mindmap(
            id=mindmap_id,
            note_id=uuid.uuid4(),
            user_id=user_id,
            structure={"id": "root", "text": "Test"},
            map_type="ai_generated",
            version=1
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mindmap
        mock_db.execute.return_value = mock_result

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db

            # Act
            result = await service.get_mindmap(mindmap_id, user_id)

            # Assert
            assert result is not None
            assert result.id == mindmap_id

    @pytest.mark.asyncio
    async def test_get_mindmap_not_found(self, mock_db):
        """Test getting a non-existent mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db

            result = await service.get_mindmap(mindmap_id, user_id)

            assert result is None

    @pytest.mark.asyncio
    async def test_update_mindmap_success(self, mock_db, mock_deepseek_service):
        """Test updating a mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()
        new_structure = {
            "id": "root",
            "text": "Updated",
            "children": []
        }

        current_mindmap = Mindmap(
            id=mindmap_id,
            note_id=uuid.uuid4(),
            user_id=user_id,
            structure={"id": "root", "text": "Old"},
            map_type="ai_generated",
            version=1
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = current_mindmap
        mock_db.execute.return_value = mock_result

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db
            service.deepseek = mock_deepseek_service

            result = await service.update_mindmap(
                mindmap_id=mindmap_id,
                user_id=user_id,
                new_structure=new_structure
            )

            assert result is not None
            mock_db.add.assert_called()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_mindmap_not_found(self, mock_db, mock_deepseek_service):
        """Test updating a non-existent mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()
        new_structure = {"id": "root", "text": "Updated"}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db
            service.deepseek = mock_deepseek_service

            result = await service.update_mindmap(
                mindmap_id=mindmap_id,
                user_id=user_id,
                new_structure=new_structure
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_delete_mindmap_success(self, mock_db):
        """Test deleting a mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_mindmap = Mindmap(
            id=mindmap_id,
            note_id=uuid.uuid4(),
            user_id=user_id,
            structure={},
            map_type="ai_generated",
            version=1
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_mindmap
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db

            result = await service.delete_mindmap(mindmap_id, user_id)

            assert result is True
            mock_db.delete.assert_called_once_with(mock_mindmap)
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_mindmap_not_found(self, mock_db):
        """Test deleting a non-existent mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db

            result = await service.delete_mindmap(mindmap_id, user_id)

            assert result is False

    @pytest.mark.asyncio
    async def test_get_mindmap_versions(self, mock_db):
        """Test getting all versions of a mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        versions = [
            Mindmap(
                id=mindmap_id,
                note_id=uuid.uuid4(),
                user_id=user_id,
                structure={},
                map_type="ai_generated",
                version=1
            ),
            Mindmap(
                id=uuid.uuid4(),
                note_id=uuid.uuid4(),
                user_id=user_id,
                structure={},
                map_type="manual",
                version=2,
                parent_version_id=mindmap_id
            )
        ]

        mock_result_scalar = MagicMock()
        mock_result_scalar.one_or_none.return_value = versions[0]

        mock_result_versions = MagicMock()
        mock_result_versions.scalars.return_value.all.return_value = versions

        mock_db.execute.return_value = mock_result_versions

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db

            # Mock get_mindmap to return original
            with patch.object(service, 'get_mindmap', return_value=versions[0]):
                result = await service.get_mindmap_versions(mindmap_id, user_id)

                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_knowledge_points(self, mock_db):
        """Test getting knowledge points for a mindmap."""
        mindmap_id = uuid.uuid4()
        user_id = uuid.uuid4()

        kps = [
            KnowledgePoint(
                id=uuid.uuid4(),
                mindmap_id=mindmap_id,
                node_id="root",
                node_path="root",
                text="Root",
                level=0
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = kps
        mock_db.execute.return_value = mock_result

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.db = mock_db

            with patch.object(service, 'get_mindmap', return_value=MagicMock()):
                result = await service.get_knowledge_points(mindmap_id, user_id)

                assert len(result) == 1
                assert result[0].node_id == "root"

    @pytest.mark.asyncio
    async def test_close_service(self, mock_db):
        """Test closing service connections."""
        mock_deepseek = MagicMock()
        mock_deepseek.close = AsyncMock()

        with patch.object(MindmapService, '__init__', lambda self, db: None):
            service = MindmapService(mock_db)
            service.deepseek = mock_deepseek

            await service.close()

            mock_deepseek.close.assert_called_once()
