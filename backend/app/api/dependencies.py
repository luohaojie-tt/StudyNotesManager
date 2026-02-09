"""Authentication dependencies."""
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.utils.jwt import verify_access_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> tuple:
    """Get current authenticated user.

    Args:
        credentials: HTTP authorization credentials
        db: Database session

    Returns:
        Tuple of (user, token_payload)

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials

    try:
        payload = verify_access_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    try:
        user = await auth_service.get_user_by_id(UUID(user_id))
        if user is None:
            raise ValueError("User not found")
        return user, payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: tuple = Depends(get_current_user),
) -> tuple:
    """Get current active user.

    Args:
        current_user: Current user tuple from get_current_user

    Returns:
        Tuple of (user, token_payload)

    Raises:
        HTTPException: If user is inactive
    """
    user, payload = current_user

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    return user, payload


async def require_verified_user(
    current_user: tuple = Depends(get_current_active_user),
) -> tuple:
    """Require verified user.

    Args:
        current_user: Current user tuple from get_current_active_user

    Returns:
        Tuple of (user, token_payload)

    Raises:
        HTTPException: If user is not verified
    """
    user, payload = current_user

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required",
        )

    return user, payload
