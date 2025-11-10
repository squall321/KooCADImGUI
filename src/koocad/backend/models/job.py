"""
Job model for CAD generation and export tasks.
"""

from __future__ import annotations

from datetime import datetime
import enum

try:
    from sqlalchemy import Column, DateTime, Enum as SQLEnum, Float, ForeignKey, Integer, String, Text, JSON
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = None  # type: ignore
    Integer = None  # type: ignore
    String = None  # type: ignore
    Text = None  # type: ignore
    Float = None  # type: ignore
    DateTime = None  # type: ignore
    ForeignKey = None  # type: ignore
    JSON = None  # type: ignore
    relationship = None  # type: ignore

from koocad.backend.database import Base


class JobType(str, enum.Enum):
    """Job type enumeration."""

    CAD_GENERATION = "cad_generation"
    EXPORT_STEP = "export_step"
    EXPORT_STL = "export_stl"
    EXPORT_IGES = "export_iges"
    EXPORT_GLB = "export_glb"
    MESHING = "meshing"


class JobStatus(str, enum.Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


if SQLALCHEMY_AVAILABLE:

    class Job(Base):
        """Job model for CAD generation and export tasks."""

        __tablename__ = "jobs"

        id = Column(Integer, primary_key=True, index=True)
        task_id = Column(String(50), unique=True, index=True)  # Celery task ID
        job_type = Column(SQLEnum(JobType), nullable=False, index=True)
        status = Column(SQLEnum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)

        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
        parameter_set_id = Column(Integer, ForeignKey("parameter_sets.id"), nullable=True)

        # Job configuration (stored as JSON)
        parameters = Column(JSON, nullable=False)

        # Results
        result_file = Column(String(255))  # MinIO object key
        error_message = Column(Text)
        progress = Column(Float, default=0.0)  # 0.0 to 100.0

        created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
        started_at = Column(DateTime)
        completed_at = Column(DateTime)

        # Relationships
        user = relationship("User", back_populates="jobs")
        project = relationship("Project", back_populates="jobs")
        parameter_set = relationship("ParameterSet", back_populates="jobs")

        def __repr__(self) -> str:
            """String representation."""
            return f"<Job(id={self.id}, type={self.job_type}, status={self.status})>"

        @property
        def duration(self) -> float | None:
            """Calculate job duration in seconds.

            Returns:
                Duration in seconds, or None if not started/completed.
            """
            if self.started_at and self.completed_at:
                return (self.completed_at - self.started_at).total_seconds()
            return None

else:

    class Job:
        """Placeholder when SQLAlchemy not available."""

        pass
