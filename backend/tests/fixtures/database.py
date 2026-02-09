"""
Database fixtures for testing.
"""
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Uses in-memory SQLite for fast tests.
    """
    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_with_data(test_db: AsyncSession) -> AsyncSession:
    """
    Create test database with sample data.
    """
    from app.models.user import User
    from app.models.note import Note
    from app.core.security import get_password_hash
    from datetime import datetime

    # Create test user
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()

    # Create test notes
    notes = [
        Note(
            title="Mathematics Note",
            content="Algebra is the study of mathematical symbols",
            subject="Mathematics",
            tags=["algebra", "symbols"],
            owner_id=user.id,
            created_at=datetime.now()
        ),
        Note(
            title="Physics Note",
            content="Newton's laws describe motion and forces",
            subject="Physics",
            tags=["newton", "motion"],
            owner_id=user.id,
            created_at=datetime.now()
        )
    ]

    for note in notes:
        test_db.add(note)

    await test_db.commit()

    return test_db
