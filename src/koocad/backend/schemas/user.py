"""
Pydantic schemas for User API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

try:
    from pydantic import BaseModel, EmailStr, Field, ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore
    EmailStr = str  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore


if PYDANTIC_AVAILABLE:

    class UserCreate(BaseModel):
        """Schema for user registration."""

        username: str = Field(..., min_length=3, max_length=50)
        email: EmailStr
        password: str = Field(..., min_length=8, max_length=100)
        full_name: Optional[str] = Field(None, max_length=100)

    class UserLogin(BaseModel):
        """Schema for user login."""

        username: str
        password: str

    class UserResponse(BaseModel):
        """Schema for user response."""

        id: int
        username: str
        email: str
        full_name: Optional[str]
        role: str
        is_active: bool
        created_at: datetime

        model_config = ConfigDict(from_attributes=True)

    class UserUpdate(BaseModel):
        """Schema for user update."""

        email: Optional[EmailStr] = None
        full_name: Optional[str] = None
        password: Optional[str] = None

    class Token(BaseModel):
        """Schema for JWT token response."""

        access_token: str
        token_type: str = "bearer"
        expires_in: int

    class TokenData(BaseModel):
        """Schema for token payload."""

        username: Optional[str] = None
        user_id: Optional[int] = None

else:

    class UserCreate:
        """Placeholder when Pydantic not available."""

        pass

    class UserLogin:
        """Placeholder when Pydantic not available."""

        pass

    class UserResponse:
        """Placeholder when Pydantic not available."""

        pass

    class UserUpdate:
        """Placeholder when Pydantic not available."""

        pass

    class Token:
        """Placeholder when Pydantic not available."""

        pass

    class TokenData:
        """Placeholder when Pydantic not available."""

        pass
