"""
Pydantic schemas for Project API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

try:
    from pydantic import BaseModel, Field, ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore


if PYDANTIC_AVAILABLE:

    class ProjectCreate(BaseModel):
        """Schema for project creation."""

        name: str = Field(..., min_length=1, max_length=100)
        description: Optional[str] = None

    class ProjectUpdate(BaseModel):
        """Schema for project update."""

        name: Optional[str] = Field(None, min_length=1, max_length=100)
        description: Optional[str] = None

    class ProjectResponse(BaseModel):
        """Schema for project response."""

        id: int
        name: str
        description: Optional[str]
        owner_id: int
        created_at: datetime
        updated_at: datetime

        model_config = ConfigDict(from_attributes=True)

else:

    class ProjectCreate:
        """Placeholder when Pydantic not available."""

        pass

    class ProjectUpdate:
        """Placeholder when Pydantic not available."""

        pass

    class ProjectResponse:
        """Placeholder when Pydantic not available."""

        pass
