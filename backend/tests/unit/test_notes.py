"""
Unit tests for notes API functionality.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime


@pytest.mark.unit
@pytest.mark.api
class TestNoteService:
    """Test note service methods."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = MagicMock()
        session.execute = MagicMock()
        session.scalar = MagicMock()
        session.scalars = MagicMock()
        session.commit = MagicMock()
        session.refresh = MagicMock()
        session.delete = MagicMock()
        return session

    @pytest.fixture
    def test_user(self):
        """Create test user."""
        from app.models.user import User

        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            hashed_password="hash",
            full_name="Test User"
        )

    @pytest.mark.asyncio
    async def test_create_note(self, mock_db_session, test_user):
        """Test creating a new note."""
        from app.services.note_service import NoteService
        from app.schemas.note import NoteCreate

        note_data = NoteCreate(
            title="Test Note",
            content="This is test content",
            subject="Mathematics",
            tags=["algebra", "equations"]
        )

        note_service = NoteService(mock_db_session)
        note = await note_service.create_note(note_data, test_user.id)

        assert note.title == "Test Note"
        assert note.content == "This is test content"
        assert note.subject == "Mathematics"
        assert note.owner_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_note_by_id(self, mock_db_session, test_user):
        """Test retrieving a note by ID."""
        from app.services.note_service import NoteService
        from app.models.note import Note

        note = Note(
            id=1,
            title="Test Note",
            content="Test content",
            subject="Math",
            owner_id=test_user.id,
            created_at=datetime.now()
        )

        mock_db_session.scalar.return_value = note

        note_service = NoteService(mock_db_session)
        retrieved_note = await note_service.get_note_by_id(1, test_user.id)

        assert retrieved_note is not None
        assert retrieved_note.id == 1
        assert retrieved_note.title == "Test Note"

    @pytest.mark.asyncio
    async def test_get_note_by_id_not_found(self, mock_db_session, test_user):
        """Test retrieving a non-existent note."""
        from app.services.note_service import NoteService

        mock_db_session.scalar.return_value = None

        note_service = NoteService(mock_db_session)
        retrieved_note = await note_service.get_note_by_id(999, test_user.id)

        assert retrieved_note is None

    @pytest.mark.asyncio
    async def test_get_note_unauthorized(self, mock_db_session, test_user):
        """Test retrieving a note owned by another user."""
        from app.services.note_service import NoteService
        from app.models.note import Note

        note = Note(
            id=1,
            title="Test Note",
            content="Test content",
            subject="Math",
            owner_id=2,  # Different user
            created_at=datetime.now()
        )

        mock_db_session.scalar.return_value = note

        note_service = NoteService(mock_db_session)
        retrieved_note = await note_service.get_note_by_id(1, test_user.id)

        # Should return None as user doesn't own this note
        assert retrieved_note is None

    @pytest.mark.asyncio
    async def test_list_notes(self, mock_db_session, test_user):
        """Test listing user's notes."""
        from app.services.note_service import NoteService
        from app.models.note import Note

        notes = [
            Note(
                id=1,
                title="Note 1",
                content="Content 1",
                subject="Math",
                owner_id=test_user.id,
                created_at=datetime.now()
            ),
            Note(
                id=2,
                title="Note 2",
                content="Content 2",
                subject="Physics",
                owner_id=test_user.id,
                created_at=datetime.now()
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = notes
        mock_db_session.execute.return_value = mock_result

        note_service = NoteService(mock_db_session)
        retrieved_notes = await note_service.list_notes(test_user.id)

        assert len(retrieved_notes) == 2
        assert retrieved_notes[0].title == "Note 1"
        assert retrieved_notes[1].title == "Note 2"

    @pytest.mark.asyncio
    async def test_update_note(self, mock_db_session, test_user):
        """Test updating a note."""
        from app.services.note_service import NoteService
        from app.models.note import Note
        from app.schemas.note import NoteUpdate

        existing_note = Note(
            id=1,
            title="Old Title",
            content="Old content",
            subject="Math",
            owner_id=test_user.id,
            created_at=datetime.now()
        )

        mock_db_session.scalar.return_value = existing_note

        update_data = NoteUpdate(
            title="Updated Title",
            content="Updated content"
        )

        note_service = NoteService(mock_db_session)
        updated_note = await note_service.update_note(1, update_data, test_user.id)

        assert updated_note.title == "Updated Title"
        assert updated_note.content == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_note(self, mock_db_session, test_user):
        """Test deleting a note."""
        from app.services.note_service import NoteService
        from app.models.note import Note

        existing_note = Note(
            id=1,
            title="Test Note",
            content="Test content",
            subject="Math",
            owner_id=test_user.id,
            created_at=datetime.now()
        )

        mock_db_session.scalar.return_value = existing_note

        note_service = NoteService(mock_db_session)
        result = await note_service.delete_note(1, test_user.id)

        assert result is True
        mock_db_session.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_notes_by_tag(self, mock_db_session, test_user):
        """Test searching notes by tag."""
        from app.services.note_service import NoteService
        from app.models.note import Note

        notes = [
            Note(
                id=1,
                title="Algebra Note",
                content="Content about algebra",
                subject="Math",
                tags=["algebra", "equations"],
                owner_id=test_user.id,
                created_at=datetime.now()
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = notes
        mock_db_session.execute.return_value = mock_result

        note_service = NoteService(mock_db_session)
        results = await note_service.search_notes(test_user.id, tag="algebra")

        assert len(results) == 1
        assert results[0].title == "Algebra Note"
        assert "algebra" in results[0].tags

    @pytest.mark.asyncio
    async def test_search_notes_by_subject(self, mock_db_session, test_user):
        """Test searching notes by subject."""
        from app.services.note_service import NoteService
        from app.models.note import Note

        notes = [
            Note(
                id=1,
                title="Math Note",
                content="Math content",
                subject="Mathematics",
                owner_id=test_user.id,
                created_at=datetime.now()
            )
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = notes
        mock_db_session.execute.return_value = mock_result

        note_service = NoteService(mock_db_session)
        results = await note_service.search_notes(test_user.id, subject="Mathematics")

        assert len(results) == 1
        assert results[0].subject == "Mathematics"


@pytest.mark.unit
@pytest.mark.api
class TestNoteValidation:
    """Test note validation and business logic."""

    @pytest.mark.asyncio
    async def test_note_title_required(self):
        """Test that note title is required."""
        from app.schemas.note import NoteCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            NoteCreate(
                title="",  # Empty title
                content="Content",
                subject="Math"
            )

    @pytest.mark.asyncio
    async def test_note_subject_validation(self):
        """Test note subject validation."""
        from app.schemas.note import NoteCreate
        from pydantic import ValidationError

        # Valid subjects
        valid_subjects = ["Mathematics", "Physics", "Chemistry", "Biology", "History"]

        for subject in valid_subjects:
            note = NoteCreate(
                title="Test",
                content="Content",
                subject=subject
            )
            assert note.subject == subject

    @pytest.mark.asyncio
    async def test_note_tags_format(self):
        """Test that tags are properly formatted."""
        from app.schemas.note import NoteCreate

        note = NoteCreate(
            title="Test",
            content="Content",
            subject="Math",
            tags=["tag1", "tag2", "tag3"]
        )

        assert len(note.tags) == 3
        assert "tag1" in note.tags

    @pytest.mark.asyncio
    async def test_note_content_length_limit(self):
        """Test note content length limit."""
        from app.schemas.note import NoteCreate
        from pydantic import ValidationError

        # Content too long (> 50000 characters)
        long_content = "x" * 50001

        with pytest.raises(ValidationError):
            NoteCreate(
                title="Test",
                content=long_content,
                subject="Math"
            )
