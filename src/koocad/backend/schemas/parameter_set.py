"""
Pydantic schemas for ParameterSet API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

try:
    from pydantic import BaseModel, Field, ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore


if PYDANTIC_AVAILABLE:

    class ParameterSetCreate(BaseModel):
        """Schema for parameter set creation."""

        name: str = Field(..., min_length=1, max_length=100)
        description: Optional[str] = None
        project_id: int
        parameters: Dict[str, Any]
        component_type: Optional[str] = Field(None, max_length=50)

    class ParameterSetUpdate(BaseModel):
        """Schema for parameter set update."""

        name: Optional[str] = Field(None, min_length=1, max_length=100)
        description: Optional[str] = None
        parameters: Optional[Dict[str, Any]] = None
        component_type: Optional[str] = None

    class ParameterSetResponse(BaseModel):
        """Schema for parameter set response."""

        id: int
        name: str
        description: Optional[str]
        project_id: int
        parameters: Dict[str, Any]
        component_type: Optional[str]
        created_at: datetime
        updated_at: datetime

        model_config = ConfigDict(from_attributes=True)

else:

    class ParameterSetCreate:
        """Placeholder when Pydantic not available."""

        pass

    class ParameterSetUpdate:
        """Placeholder when Pydantic not available."""

        pass

    class ParameterSetResponse:
        """Placeholder when Pydantic not available."""

        pass
