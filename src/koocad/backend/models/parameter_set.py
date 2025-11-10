"""
ParameterSet model for saving parameter configurations.
"""

from __future__ import annotations

from datetime import datetime

try:
    from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
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
    JSON = None  # type: ignore
    relationship = None  # type: ignore

from koocad.backend.database import Base


if SQLALCHEMY_AVAILABLE:

    class ParameterSet(Base):
        """ParameterSet model for saving parameter configurations."""

        __tablename__ = "parameter_sets"

        id = Column(Integer, primary_key=True, index=True)
        name = Column(String(100), nullable=False, index=True)
        description = Column(Text)
        project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

        # Parameters stored as JSON
        # Example: {"substrate_width": 12.0, "ball_pitch": 0.8, ...}
        parameters = Column(JSON, nullable=False)

        # Component type (BGA, MLCC, etc.)
        component_type = Column(String(50), index=True)

        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relationships
        project = relationship("Project", back_populates="parameter_sets")
        jobs = relationship("Job", back_populates="parameter_set")

        def __repr__(self) -> str:
            """String representation."""
            return f"<ParameterSet(id={self.id}, name='{self.name}', type={self.component_type})>"

else:

    class ParameterSet:
        """Placeholder when SQLAlchemy not available."""

        pass
