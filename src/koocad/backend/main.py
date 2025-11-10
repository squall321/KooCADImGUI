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

    # Add custom middleware
    try:
        from koocad.backend.middleware.metrics import MetricsMiddleware
        from koocad.backend.middleware.rate_limit import RateLimitMiddleware

        app.add_middleware(MetricsMiddleware)
        # app.add_middleware(RateLimitMiddleware)  # Enable when Redis is available
    except ImportError as e:
        print(f"Warning: Could not load middleware: {e}")

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
        # Check database connectivity
        db_status = "ok"
        try:
            from sqlalchemy import text
            from koocad.backend.database import async_engine
            async with async_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"error: {e}"

        # Check Redis connectivity
        redis_status = "ok"
        try:
            import redis.asyncio as redis
            r = redis.from_url(settings.redis_url)
            await r.ping()
            await r.close()
        except Exception as e:
            redis_status = f"error: {e}"

        overall_status = "ready" if db_status == "ok" and redis_status == "ok" else "degraded"

        return {
            "status": overall_status,
            "database": db_status,
            "redis": redis_status,
        }

    @app.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint.

        Returns:
            Prometheus metrics in text format.
        """
        from koocad.backend.middleware.metrics import get_metrics

        metrics_data, content_type = get_metrics()
        return Response(content=metrics_data, media_type=content_type)

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
