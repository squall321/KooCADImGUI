"""
Configuration management using pydantic-settings.

This module provides centralized configuration with environment variable support.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = Field(
        default="postgresql://koocad:koocad@localhost:5432/koocad",
        description="PostgreSQL connection URL",
    )
    echo: bool = Field(default=False, description="Echo SQL queries")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Max connections overflow")

    model_config = SettingsConfigDict(env_prefix="DATABASE_")


class RedisSettings(BaseSettings):
    """Redis configuration."""

    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    max_connections: int = Field(default=10, description="Max connections in pool")

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class MinIOSettings(BaseSettings):
    """MinIO (S3-compatible) storage configuration."""

    endpoint: str = Field(default="localhost:9000", description="MinIO endpoint")
    access_key: str = Field(default="koocad", description="Access key")
    secret_key: str = Field(default="koocad_secret", description="Secret key")
    secure: bool = Field(default=False, description="Use HTTPS")
    bucket_cad_files: str = Field(default="cad-files", description="CAD files bucket")
    bucket_exports: str = Field(default="exports", description="Exports bucket")
    bucket_meshes: str = Field(default="meshes", description="Meshes bucket")

    model_config = SettingsConfigDict(env_prefix="MINIO_")


class CelerySettings(BaseSettings):
    """Celery task queue configuration."""

    broker_url: str = Field(
        default="redis://localhost:6379/1",
        description="Celery broker URL",
    )
    result_backend: str = Field(
        default="redis://localhost:6379/2",
        description="Celery result backend URL",
    )
    task_serializer: str = Field(default="json", description="Task serializer")
    result_serializer: str = Field(default="json", description="Result serializer")
    accept_content: list[str] = Field(
        default=["json"], description="Accepted content types"
    )
    timezone: str = Field(default="UTC", description="Timezone")
    enable_utc: bool = Field(default=True, description="Enable UTC")

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format (json or console)")
    file: Optional[Path] = Field(default=None, description="Log file path")

    model_config = SettingsConfigDict(env_prefix="LOG_")


class TracingSettings(BaseSettings):
    """OpenTelemetry tracing configuration."""

    enabled: bool = Field(default=False, description="Enable tracing")
    otlp_endpoint: Optional[str] = Field(
        default=None, description="OTLP collector endpoint"
    )
    service_name: str = Field(default="koocad", description="Service name")

    model_config = SettingsConfigDict(env_prefix="TRACING_")


class SecuritySettings(BaseSettings):
    """Security configuration."""

    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for encryption",
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(
        default=60, description="JWT expiration time (minutes)"
    )
    api_key_header: str = Field(
        default="X-API-Key", description="API key header name"
    )

    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class CADSettings(BaseSettings):
    """CAD kernel configuration."""

    default_kernel: str = Field(
        default="cadquery", description="Default CAD kernel (cadquery or occt)"
    )
    kernel_switch_threshold: int = Field(
        default=100, description="Shape count threshold for switching to OCCT"
    )
    tessellation_quality: float = Field(
        default=0.1, description="Tessellation tolerance"
    )
    cache_enabled: bool = Field(default=True, description="Enable shape caching")
    cache_max_size_mb: int = Field(
        default=1000, description="Max cache size (MB)"
    )

    model_config = SettingsConfigDict(env_prefix="CAD_")


class MeshSettings(BaseSettings):
    """Mesh generation configuration."""

    default_engine: str = Field(
        default="gmsh", description="Default mesh engine (gmsh or netgen)"
    )
    min_element_size: float = Field(
        default=0.1, description="Minimum element size (mm)"
    )
    max_element_size: float = Field(
        default=5.0, description="Maximum element size (mm)"
    )
    quality_threshold: float = Field(
        default=0.6, description="Mesh quality threshold"
    )

    model_config = SettingsConfigDict(env_prefix="MESH_")


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = Field(default="KooCAD", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    environment: str = Field(default="development", description="Environment")

    # Sub-settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    tracing: TracingSettings = Field(default_factory=TracingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    cad: CADSettings = Field(default_factory=CADSettings)
    mesh: MeshSettings = Field(default_factory=MeshSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance.

    Returns:
        Settings instance.

    Example:
        >>> settings = get_settings()
        >>> print(settings.database.url)
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment.

    Returns:
        New settings instance.
    """
    global _settings
    _settings = Settings()
    return _settings
