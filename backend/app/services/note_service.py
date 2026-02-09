"""Note service for note management."""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate


class NoteService:
    """Service for note management."""

    def __init__(self, db: AsyncSession):
        """Initialize note service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_note(
        self,
        user_id: uuid.UUID,
        note_data: NoteCreate,
    ) -> Note:
        """Create a new note.

        Args:
            user_id: User ID
            note_data: Note creation data

        Returns:
            Created note
        """
        new_note = Note(
            user_id=user_id,
            title=note_data.title,
            content=note_data.content,
            file_url=note_data.file_url,
            thumbnail_url=note_data.thumbnail_url,
            ocr_text=note_data.ocr_text,
            category_id=note_data.category_id,
            tags=note_data.tags,
            metadata=note_data.metadata,
        )

        self.db.add(new_note)
        await self.db.commit()
        await self.db.refresh(new_note)

        return new_note

    async def get_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Note]:
        """Get note by ID.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Note if found and belongs to user, None otherwise
        """
        result = await self.db.execute(
            select(Note)
            .where(Note.id == note_id)
            .where(Note.user_id == user_id)
            .options(selectinload(Note.category))
        )
        return result.scalar_one_or_none()

    async def get_notes(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> tuple[list[Note], int]:
        """Get notes for user with pagination and filters.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            category_id: Filter by category ID
            search: Search in title and content
            tags: Filter by tags

        Returns:
            Tuple of (notes list, total count)
        """
        # Build query
        query = select(Note).where(Note.user_id == user_id)

        if category_id:
            query = query.where(Note.category_id == category_id)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (Note.title.ilike(search_pattern)) | (Note.content.ilike(search_pattern))
            )

        if tags:
            query = query.where(Note.tags.overlap(tags))

        # Get total count
        count_query = select(Note.id).where(Note.user_id == user_id)
        if category_id:
            count_query = count_query.where(Note.category_id == category_id)
        if search:
            search_pattern = f"%{search}%"
            count_query = count_query.where(
                (Note.title.ilike(search_pattern)) | (Note.content.ilike(search_pattern))
            )
        if tags:
            count_query = count_query.where(Note.tags.overlap(tags))

        count_result = await self.db.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.order_by(Note.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        notes = result.scalars().all()

        return list(notes), total

    async def update_note(
        self,
        note_id: uuid.UUID,
        user_id: uuid.UUID,
        note_data: NoteUpdate,
    ) -> Optional[Note]:
        """Update note.

        Args:
            note_id: Note ID
            user_id: User ID
            note_data: Note update data

        Returns:
            Updated note if found, None otherwise
        """
        note = await self.get_note(note_id, user_id)
        if not note:
            return None

        # Update fields
        update_data = note_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(note, field, value)

        await self.db.commit()
        await self.db.refresh(note)

        return note

    async def delete_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete note.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            True if deleted, False otherwise
        """
        note = await self.get_note(note_id, user_id)
        if not note:
            return False

        await self.db.delete(note)
        await self.db.commit()

        return True

    async def toggle_favorite(
        self, note_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[Note]:
        """Toggle note favorite status.

        Args:
            note_id: Note ID
            user_id: User ID

        Returns:
            Updated note if found, None otherwise
        """
        note = await self.get_note(note_id, user_id)
        if not note:
            return None

        note.is_favorited = not note.is_favorited
        await self.db.commit()
        await self.db.refresh(note)

        return note
