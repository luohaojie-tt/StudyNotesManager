"""Mindmap generation service."""

import uuid
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mindmap import Mindmap, KnowledgePoint
from app.services.deepseek_service import DeepSeekService
from app.core.config import get_settings

settings = get_settings()


class MindmapService:
    """Service for generating and managing mindmaps."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize mindmap service.

        Args:
            db: Database session
        """
        self.db = db
        self.deepseek = DeepSeekService()

    async def generate_mindmap(
        self,
        note_id: uuid.UUID,
        user_id: uuid.UUID,
        note_content: str,
        note_title: str,
    ) -> Mindmap:
        """Generate mindmap from note content.

        Args:
            note_id: Note ID
            user_id: User ID
            note_content: Note text content
            note_title: Note title

        Returns:
            Created mindmap

        Raises:
            ValueError: If generation fails
        """
        try:
            # Generate mindmap structure using DeepSeek
            logger.info(f"Generating mindmap for note {note_id}")
            structure = await self.deepseek.generate_mindmap(
                note_content=note_content,
                note_title=note_title,
                max_levels=settings.MINDMAP_MAX_LEVELS,
            )

            # Create mindmap record
            mindmap = Mindmap(
                id=uuid.uuid4(),
                note_id=note_id,
                user_id=user_id,
                structure=structure,
                map_type="ai_generated",
                ai_model="deepseek-chat",
                version=1,
            )

            self.db.add(mindmap)
            await self.db.flush()

            # Extract and save knowledge points
            await self._extract_and_save_knowledge_points(mindmap, structure)

            await self.db.commit()
            await self.db.refresh(mindmap)

            logger.info(f"Successfully generated mindmap {mindmap.id} for note {note_id}")
            return mindmap

        except Exception as e:
            logger.error(f"Failed to generate mindmap for note {note_id}: {e}")
            await self.db.rollback()
            raise

    async def _extract_and_save_knowledge_points(
        self,
        mindmap: Mindmap,
        structure: Dict[str, Any],
        parent_node_id: Optional[str] = None,
        node_path: str = "root",
        level: int = 1,
    ) -> None:
        """Extract and save knowledge points from mindmap structure.

        Args:
            mindmap: Mindmap instance
            structure: Mindmap node structure
            parent_node_id: Parent node ID
            node_path: Current node path
            level: Current hierarchy level
        """
        # Create knowledge point for this node
        knowledge_point = KnowledgePoint(
            id=uuid.uuid4(),
            mindmap_id=mindmap.id,
            node_id=structure["id"],
            node_path=node_path,
            text=structure["text"],
            level=level,
            parent_node_id=parent_node_id,
        )

        self.db.add(knowledge_point)

        # Recursively process children
        for child in structure.get("children", []):
            child_path = f"{node_path}/{child['id']}"
            await self._extract_and_save_knowledge_points(
                mindmap,
                child,
                structure["id"],
                child_path,
                level + 1,
            )

    async def get_mindmap(
        self,
        mindmap_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Mindmap]:
        """Get mindmap by ID.

        Args:
            mindmap_id: Mindmap ID
            user_id: User ID (for authorization)

        Returns:
            Mindmap if found and authorized, None otherwise
        """
        result = await self.db.execute(
            select(Mindmap).where(
                Mindmap.id == mindmap_id,
                Mindmap.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_mindmap(
        self,
        mindmap_id: uuid.UUID,
        user_id: uuid.UUID,
        new_structure: Dict[str, Any],
    ) -> Optional[Mindmap]:
        """Update mindmap structure (creates new version).

        Args:
            mindmap_id: Mindmap ID
            user_id: User ID
            new_structure: New mindmap structure

        Returns:
            Updated mindmap, None if not found

        Raises:
            ValueError: If structure is invalid
        """
        # Get current mindmap
        current = await self.get_mindmap(mindmap_id, user_id)
        if not current:
            return None

        try:
            # Validate new structure
            self.deepseek._validate_mindmap_structure(
                new_structure,
                settings.MINDMAP_MAX_LEVELS,
            )

            # Create new version
            new_version = Mindmap(
                id=uuid.uuid4(),
                note_id=current.note_id,
                user_id=user_id,
                structure=new_structure,
                map_type="manual",
                version=current.version + 1,
                parent_version_id=mindmap_id,
            )

            self.db.add(new_version)
            await self.db.flush()

            # Extract and save knowledge points for new version
            await self._extract_and_save_knowledge_points(new_version, new_structure)

            await self.db.commit()
            await self.db.refresh(new_version)

            logger.info(f"Created mindmap version {new_version.version} for note {current.note_id}")
            return new_version

        except Exception as e:
            logger.error(f"Failed to update mindmap {mindmap_id}: {e}")
            await self.db.rollback()
            raise

    async def get_mindmap_versions(
        self,
        mindmap_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[Mindmap]:
        """Get all versions of a mindmap.

        Args:
            mindmap_id: Original mindmap ID
            user_id: User ID

        Returns:
            List of mindmap versions ordered by version number
        """
        # Get original mindmap
        original = await self.get_mindmap(mindmap_id, user_id)
        if not original:
            return []

        # Get all versions (original + descendants)
        result = await self.db.execute(
            select(Mindmap)
            .where(
                (Mindmap.id == mindmap_id) | (Mindmap.parent_version_id == mindmap_id)
            )
            .order_by(Mindmap.version)
        )
        return list(result.scalars().all())

    async def delete_mindmap(
        self,
        mindmap_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Delete mindmap.

        Args:
            mindmap_id: Mindmap ID
            user_id: User ID

        Returns:
            True if deleted, False if not found
        """
        mindmap = await self.get_mindmap(mindmap_id, user_id)
        if not mindmap:
            return False

        await self.db.delete(mindmap)
        await self.db.commit()

        logger.info(f"Deleted mindmap {mindmap_id}")
        return True

    async def get_knowledge_points(
        self,
        mindmap_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> List[KnowledgePoint]:
        """Get knowledge points for a mindmap.

        Args:
            mindmap_id: Mindmap ID
            user_id: User ID

        Returns:
            List of knowledge points

        Raises:
            ValueError: If mindmap not found or unauthorized
        """
        # Verify authorization
        mindmap = await self.get_mindmap(mindmap_id, user_id)
        if not mindmap:
            raise ValueError("Mindmap not found or unauthorized")

        result = await self.db.execute(
            select(KnowledgePoint)
            .where(KnowledgePoint.mindmap_id == mindmap_id)
            .order_by(KnowledgePoint.node_path)
        )
        return list(result.scalars().all())

    async def close(self) -> None:
        """Close service connections."""
        await self.deepseek.close()
