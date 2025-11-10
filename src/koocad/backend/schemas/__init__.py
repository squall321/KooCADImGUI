"""
Pydantic schemas for request/response validation.

Schemas:
    - User schemas: Login, registration, profile
    - Project schemas: Create, update, list
    - Job schemas: Create, status, results
    - ParameterSet schemas: Save, load, list
"""

from __future__ import annotations

try:
    from koocad.backend.schemas.user import (
        UserCreate,
        UserLogin,
        UserResponse,
        Token,
    )
    from koocad.backend.schemas.project import (
        ProjectCreate,
        ProjectUpdate,
        ProjectResponse,
    )
    from koocad.backend.schemas.job import (
        JobCreate,
        JobResponse,
        JobStatus,
    )
    from koocad.backend.schemas.parameter_set import (
        ParameterSetCreate,
        ParameterSetUpdate,
        ParameterSetResponse,
    )
except ImportError:
    # Schemas not yet created
    pass

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "JobCreate",
    "JobResponse",
    "JobStatus",
    "ParameterSetCreate",
    "ParameterSetUpdate",
    "ParameterSetResponse",
]
