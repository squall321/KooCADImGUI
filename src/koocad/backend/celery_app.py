"""
Celery application for async task processing.

This module configures Celery for:
- CAD generation tasks
- Export tasks (STEP, STL, IGES, GLB)
- Meshing tasks
- Parameter sweeps

Broker: Redis
Backend: Redis

Usage:
    # Start worker
    celery -A koocad.backend.celery_app worker --loglevel=info

    # Start with multiple workers
    celery -A koocad.backend.celery_app worker --loglevel=info --concurrency=4

    # Start Flower monitoring
    celery -A koocad.backend.celery_app flower
"""

from __future__ import annotations

try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None  # type: ignore

from koocad.backend.config import get_settings

settings = get_settings()

if CELERY_AVAILABLE:
    # Create Celery app
    celery_app = Celery(
        "koocad",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )

    # Configure Celery
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max
        task_soft_time_limit=3300,  # 55 minutes soft limit
        worker_prefetch_multiplier=1,  # Fair task distribution
        worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    )

    # Task routing (different queues for different task types)
    celery_app.conf.task_routes = {
        "koocad.backend.tasks.cad_tasks.*": {"queue": "cad_generation"},
        "koocad.backend.tasks.export_tasks.*": {"queue": "export"},
        "koocad.backend.tasks.mesh_tasks.*": {"queue": "meshing"},
    }

    # Auto-discover tasks
    celery_app.autodiscover_tasks(["koocad.backend.tasks"])

else:
    celery_app = None  # type: ignore
