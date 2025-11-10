#!/usr/bin/env python
"""
KooCAD Backend API Demo.

This example demonstrates the FastAPI backend with:
- RESTful API endpoints for projects, jobs, parameters
- JWT authentication
- WebSocket real-time updates
- Swagger UI documentation

Phase 106-109 Complete:
- FastAPI project structure
- Database models (User, Project, Job, ParameterSet)
- Pydantic schemas for validation
- Authentication with JWT tokens
- CRUD endpoints for all resources
- WebSocket for real-time job updates

Requirements:
    pip install fastapi uvicorn[standard] sqlalchemy asyncpg pydantic-settings
    pip install python-jose[cryptography] passlib[bcrypt] python-multipart

Usage:
    # Start the server
    python examples/10_backend_api_demo.py

    # Or with uvicorn directly
    uvicorn koocad.backend.main:app --reload

    # Then visit:
    # - http://localhost:8000/docs (Swagger UI)
    # - http://localhost:8000/redoc (ReDoc)
    # - http://localhost:8000/ (API info)

API Endpoints:
    Authentication:
        POST /api/v1/auth/register - Register new user
        POST /api/v1/auth/login - Login and get JWT token
        GET /api/v1/auth/me - Get current user info

    Projects:
        POST /api/v1/projects/ - Create project
        GET /api/v1/projects/ - List projects
        GET /api/v1/projects/{id} - Get project details
        PUT /api/v1/projects/{id} - Update project
        DELETE /api/v1/projects/{id} - Delete project

    Jobs:
        POST /api/v1/jobs/ - Submit CAD generation job
        GET /api/v1/jobs/ - List jobs
        GET /api/v1/jobs/{id} - Get job status
        POST /api/v1/jobs/{id}/cancel - Cancel job
        DELETE /api/v1/jobs/{id} - Delete job

    Parameters:
        POST /api/v1/parameters/ - Save parameter set
        GET /api/v1/parameters/ - List parameter sets
        GET /api/v1/parameters/{id} - Get parameter set
        PUT /api/v1/parameters/{id} - Update parameter set
        DELETE /api/v1/parameters/{id} - Delete parameter set

    WebSocket:
        WS /ws/{user_id} - Real-time job updates

Example Workflow:
    1. Register user: POST /api/v1/auth/register
    2. Login: POST /api/v1/auth/login (get token)
    3. Create project: POST /api/v1/projects/ (with Bearer token)
    4. Save parameters: POST /api/v1/parameters/
    5. Submit job: POST /api/v1/jobs/
    6. Monitor via WebSocket: WS /ws/{user_id}
    7. Get result: GET /api/v1/jobs/{job_id}

Database:
    The demo uses PostgreSQL. Make sure to configure DATABASE_URL in .env:
    DATABASE_URL=postgresql://koocad:koocad@localhost:5432/koocad

    Or the app will try to use the default connection string.

Next Steps (Phase 110-120):
    - Celery job queue for async CAD generation
    - MinIO integration for file storage
    - Rate limiting and API keys
    - Prometheus metrics
    - Health checks with dependency status
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from koocad.backend.main import main

    if __name__ == "__main__":
        print("=" * 70)
        print("KooCAD Backend API - FastAPI Demo")
        print("=" * 70)
        print("\nPhase 106-109 Complete:")
        print("  ✓ FastAPI project structure")
        print("  ✓ SQLAlchemy database models")
        print("  ✓ Pydantic schemas")
        print("  ✓ JWT authentication")
        print("  ✓ RESTful API endpoints")
        print("  ✓ WebSocket real-time updates")
        print("\nStarting server...")
        print("Visit http://localhost:8000/docs for API documentation")
        print("\nNote: PostgreSQL database required")
        print("Set DATABASE_URL in .env or use default connection")
        print("=" * 70 + "\n")

        main()

except ImportError as e:
    print("Error: Required dependencies not installed.")
    print("\nTo install dependencies, run:")
    print("  pip install fastapi uvicorn[standard] sqlalchemy asyncpg")
    print("  pip install pydantic-settings python-jose[cryptography] passlib[bcrypt]")
    print(f"\nDetails: {e}")
    sys.exit(1)
