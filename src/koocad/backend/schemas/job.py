"""
Pydantic schemas for Job API.
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

from koocad.backend.models.job import JobType, JobStatus


if PYDANTIC_AVAILABLE:

    class JobCreate(BaseModel):
        """Schema for job creation."""

        job_type: JobType
        parameters: Dict[str, Any]
        project_id: Optional[int] = None
        parameter_set_id: Optional[int] = None

    class JobResponse(BaseModel):
        """Schema for job response."""

        id: int
        task_id: Optional[str]
        job_type: JobType
        status: JobStatus
        parameters: Dict[str, Any]
        result_file: Optional[str]
        error_message: Optional[str]
        progress: float
        created_at: datetime
        started_at: Optional[datetime]
        completed_at: Optional[datetime]

        model_config = ConfigDict(from_attributes=True)

    class JobStatusUpdate(BaseModel):
        """Schema for job status update (internal)."""

        status: JobStatus
        progress: float = 0.0
        error_message: Optional[str] = None
        result_file: Optional[str] = None

else:

    class JobCreate:
        """Placeholder when Pydantic not available."""

        pass

    class JobResponse:
        """Placeholder when Pydantic not available."""

        pass

    class JobStatusUpdate:
        """Placeholder when Pydantic not available."""

        pass
