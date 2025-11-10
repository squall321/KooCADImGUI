"""
KooCAD Backend - FastAPI application.

Main entry point for the CAD generation orchestrator.

Run with:
    uvicorn koocad.backend.main:app --reload

Or:
    python -m koocad.backend.main
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None  # type: ignore
    CORSMiddleware = None  # type: ignore
    JSONResponse = None  # type: ignore

from koocad.backend.config import get_settings
from koocad.backend.database import init_db

settings = get_settings()


if FASTAPI_AVAILABLE:

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Lifespan context manager for startup/shutdown events.

        Args:
            app: FastAPI application instance.

        Yields:
            None
        """
        # Startup
        print("=" * 70)
        print(f"{settings.app_name} v{settings.app_version}")
        print("=" * 70)
        print("Initializing database...")
        await init_db()
        print("Database initialized.")
        print(f"Server starting on http://0.0.0.0:8000")
        print(f"API docs available at http://0.0.0.0:8000/docs")
        print("=" * 70)

        yield

        # Shutdown
        print("Shutting down...")

    # Create FastAPI application
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Parametric CAD generation API for electronic components",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root endpoint
    @app.get("/")
    async def root() -> dict:
        """Root endpoint.

        Returns:
            Welcome message with API info.
        """
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
        }

    # Health check endpoints
    @app.get("/health")
    async def health() -> dict:
        """Health check endpoint (liveness probe).

        Returns:
            Health status.
        """
        return {"status": "healthy"}

    @app.get("/ready")
    async def ready() -> dict:
        """Readiness check endpoint.

        Returns:
            Readiness status with dependency checks.
        """
        # TODO: Add actual dependency checks (DB, Redis, etc.)
        return {
            "status": "ready",
            "database": "ok",
            "redis": "ok",
        }

    # Include routers
    try:
        from koocad.backend.routers import auth, projects, jobs, parameters, websocket

        app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
        app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
        app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
        app.include_router(parameters.router, prefix="/api/v1/parameters", tags=["parameters"])
        app.include_router(websocket.router, tags=["websocket"])
    except ImportError as e:
        print(f"Warning: Could not import some routers: {e}")

else:
    app = None  # type: ignore


def main() -> None:
    """Run application with uvicorn."""
    if not FASTAPI_AVAILABLE:
        print("Error: FastAPI is not installed.")
        print("\nTo install FastAPI and dependencies, run:")
        print("  pip install fastapi uvicorn[standard] sqlalchemy asyncpg pydantic-settings")
        return

    import uvicorn

    uvicorn.run(
        "koocad.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
