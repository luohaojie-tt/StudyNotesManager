"""
Test utilities and helper functions.
"""
import asyncio
from typing import Any, Dict, Optional
from httpx import AsyncClient, ASGITransport
from app.main import app


async def create_test_user(
    client: AsyncClient,
    email: str = "test@example.com",
    username: str = "testuser",
    password: str = "TestPass123!"
) -> Dict[str, Any]:
    """
    Create a test user and return user data.

    Args:
        client: Test HTTP client
        email: User email
        username: Username
        password: Password

    Returns:
        Created user data
    """
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password,
            "full_name": "Test User"
        }
    )
    return response.json()


async def authenticate_user(
    client: AsyncClient,
    username: str = "testuser",
    password: str = "TestPass123!"
) -> str:
    """
    Authenticate user and return access token.

    Args:
        client: Test HTTP client
        username: Username
        password: Password

    Returns:
        JWT access token
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password}
    )
    return response.json()["access_token"]


async def create_test_note(
    client: AsyncClient,
    headers: Dict[str, str],
    title: str = "Test Note",
    content: str = "Test content",
    subject: str = "Mathematics",
    tags: Optional[list] = None
) -> Dict[str, Any]:
    """
    Create a test note.

    Args:
        client: Test HTTP client
        headers: Auth headers
        title: Note title
        content: Note content
        subject: Note subject
        tags: Note tags

    Returns:
        Created note data
    """
    note_data = {
        "title": title,
        "content": content,
        "subject": subject,
        "tags": tags or []
    }

    response = await client.post(
        "/api/v1/notes",
        headers=headers,
        json=note_data
    )
    return response.json()


def assert_valid_note(note: Dict[str, Any]) -> None:
    """
    Assert that note data is valid.

    Args:
        note: Note data to validate
    """
    assert "id" in note
    assert "title" in note
    assert "content" in note
    assert "subject" in note
    assert "created_at" in note
    assert isinstance(note["title"], str)
    assert isinstance(note["content"], str)
    assert len(note["title"]) > 0


def assert_valid_user(user: Dict[str, Any]) -> None:
    """
    Assert that user data is valid.

    Args:
        user: User data to validate
    """
    assert "id" in user
    assert "email" in user
    assert "username" in user
    assert "hashed_password" not in user  # Should never expose
    assert "@" in user["email"]


def assert_valid_mindmap(mindmap: Dict[str, Any]) -> None:
    """
    Assert that mindmap data is valid.

    Args:
        mindmap: Mindmap data to validate
    """
    assert "nodes" in mindmap
    assert "edges" in mindmap
    assert len(mindmap["nodes"]) > 0

    # Validate nodes
    for node in mindmap["nodes"]:
        assert "id" in node
        assert "label" in node
        assert "level" in node

    # Validate edges
    node_ids = {n["id"] for n in mindmap["nodes"]}
    for edge in mindmap["edges"]:
        assert "from" in edge
        assert "to" in edge
        assert edge["from"] in node_ids
        assert edge["to"] in node_ids


async def wait_for_condition(
    condition: callable,
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """
    Wait for a condition to become true.

    Args:
        condition: Callable that returns bool
        timeout: Maximum wait time in seconds
        interval: Check interval in seconds

    Returns:
        True if condition met, False if timeout
    """
    start = asyncio.get_event_loop().time()

    while asyncio.get_event_loop().time() - start < timeout:
        if condition():
            return True
        await asyncio.sleep(interval)

    return False
