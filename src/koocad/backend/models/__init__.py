"""
SQLAlchemy database models.

Models:
    - User: User accounts with authentication
    - Project: CAD projects with parameter sets
    - Job: CAD generation or export jobs
    - ParameterSet: Saved parameter configurations
"""

from __future__ import annotations

try:
    from koocad.backend.models.user import User
    from koocad.backend.models.project import Project
    from koocad.backend.models.job import Job
    from koocad.backend.models.parameter_set import ParameterSet
except ImportError:
    # Models not yet created
    pass

__all__ = ["User", "Project", "Job", "ParameterSet"]
