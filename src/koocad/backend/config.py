"""
Configuration settings for KooCAD backend.

Environment variables:
    DATABASE_URL: PostgreSQL connection string
    REDIS_URL: Redis connection string for Celery broker
    JWT_SECRET_KEY: Secret key for JWT token signing
    MINIO_ENDPOINT: MinIO endpoint for file storage
    MINIO_ACCESS_KEY: MinIO access key
    MINIO_SECRET_KEY: MinIO secret key
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings  # type: ignore
    except ImportError:
        BaseSettings = object  # type: ignore


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "KooCAD Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://koocad:koocad@localhost:5432/koocad"

    # Redis (Celery broker)
    redis_url: str = "redis://localhost:6379/0"

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    # MinIO Object Storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "koocad"
    minio_secure: bool = False

    # API Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 100

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]

    # Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance.
    """
    return Settings()
