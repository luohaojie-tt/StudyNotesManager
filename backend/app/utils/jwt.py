"""JWT utility functions."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token.

    Args:
        data: Data to encode in token

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def verify_access_token(token: str) -> dict:
    """Verify access token.

    Args:
        token: Access token to verify

    Returns:
        Token payload if valid

    Raises:
        JWTError: If token is invalid, expired, or not an access token
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise JWTError("Invalid token type")
    return payload


def verify_refresh_token(token: str) -> dict:
    """Verify refresh token.

    Args:
        token: Refresh token to verify

    Returns:
        Token payload if valid

    Raises:
        JWTError: If token is invalid, expired, or not a refresh token
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Invalid token type")
    return payload


def verify_token(token: str) -> dict:
    """Verify any JWT token (access, refresh, or verification).

    Args:
        token: JWT token to verify

    Returns:
        Token payload if valid

    Raises:
        JWTError: If token is invalid or expired
    """
    return decode_token(token)


def create_verification_token(email: str) -> str:
    """Create a verification token for email verification.

    Args:
        email: User email to verify

    Returns:
        Encoded JWT verification token
    """
    to_encode = {"sub": email, "type": "verification"}
    expire = datetime.utcnow() + timedelta(days=7)  # Valid for 7 days
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
