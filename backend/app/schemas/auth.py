"""Authentication schemas for request/response validation."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password meets strong security requirements.
        
        Requirements:
        - Minimum 12 characters
        - At least one lowercase letter
        - At least one uppercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")
        
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?`~" for c in v):
            raise ValueError("Password must contain at least one special character")
        
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
    id: UUID
    email: str
    full_name: Optional[str] = None
    subscription_tier: str = "free"
    is_verified: bool = False
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserWithTokenResponse(UserResponse):
    """User response with tokens schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900
