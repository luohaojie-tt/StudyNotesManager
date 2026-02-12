"""Authentication schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets security requirements.

        Requirements:
        - Minimum 8 characters
        - At least one letter
        - At least one digit
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class UserResponse(BaseModel):
    """User response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: Optional[str] = None
    subscription_tier: str = "free"
    is_verified: bool = False
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserWithTokenResponse(UserResponse):
    """User response with tokens schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
