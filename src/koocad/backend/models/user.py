"""
User model for authentication and authorization.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

try:
    from sqlalchemy import Boolean, Column, DateTime, Integer, String, Enum as SQLEnum
    from sqlalchemy.orm import relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    Column = None  # type: ignore
    Integer = None  # type: ignore
    String = None  # type: ignore
    Boolean = None  # type: ignore
    DateTime = None  # type: ignore
    relationship = None  # type: ignore

import enum

from koocad.backend.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


if SQLALCHEMY_AVAILABLE:

    class User(Base):
        """User model for authentication."""

        __tablename__ = "users"

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String(50), unique=True, index=True, nullable=False)
        email = Column(String(100), unique=True, index=True, nullable=False)
        hashed_password = Column(String(255), nullable=False)
        full_name = Column(String(100))
        role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
        is_active = Column(Boolean, default=True, nullable=False)
        api_key = Column(String(64), unique=True, index=True)

        created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        # Relationships
        projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
        jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

        def __repr__(self) -> str:
            """String representation."""
            return f"<User(id={self.id}, username='{self.username}', role={self.role})>"

else:

    class User:
        """Placeholder when SQLAlchemy not available."""

        pass
