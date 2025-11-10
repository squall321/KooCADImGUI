"""
Database configuration and session management.

Uses SQLAlchemy async engine for PostgreSQL.
"""

from __future__ import annotations

from typing import AsyncGenerator

try:
    from sqlalchemy import create_engine
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.orm import declarative_base, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    AsyncSession = None  # type: ignore
    declarative_base = None  # type: ignore

from koocad.backend.config import get_settings

settings = get_settings()

# SQLAlchemy Base
if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
else:
    Base = object  # type: ignore

# Async engine for modern FastAPI
if SQLALCHEMY_AVAILABLE:
    # Convert postgresql:// to postgresql+asyncpg://
    async_database_url = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )

    async_engine = create_async_engine(
        async_database_url,
        echo=settings.debug,
        future=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Sync engine for Alembic migrations
    sync_engine = create_engine(
        settings.database_url,
        echo=settings.debug,
    )

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=sync_engine,
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session.

    Yields:
        AsyncSession instance.
    """
    if not SQLALCHEMY_AVAILABLE:
        raise ImportError("SQLAlchemy is required. Install with: pip install sqlalchemy")

    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables).

    Note: In production, use Alembic migrations instead.
    """
    if not SQLALCHEMY_AVAILABLE:
        return

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
