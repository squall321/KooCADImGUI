"""
Project model for organizing CAD work.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

try:
    from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = None  # type: ignore
    Integer = None  # type: ignore
    String = None  # type: ignore
    Text = None  # type: ignore
    DateTime = None  # type: ignore
    ForeignKey = None  # type: ignore
    relationship = None  # type: ignore

from koocad.backend.database import Base


if SQLALCHEMY_AVAILABLE:

    class Project(Base):
        """Project model for organizing CAD work."""

        __tablename__ = "projects"

        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(100), nullable=False, index=True)
        description = Column(Text)
        owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relationships
        owner = relationship("User", back_populates="projects")
        parameter_sets = relationship(
            "ParameterSet", back_populates="project", cascade="all, delete-orphan"
        )
        jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

        def __repr__(self) -> str:
            """String representation."""
            return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"

else:

    class Project:
        """Placeholder when SQLAlchemy not available."""

        pass
