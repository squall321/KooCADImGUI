"""
Prometheus metrics collection.

This module provides decorators and utilities for collecting application
metrics (counters, histograms, gauges) for monitoring.
"""

import functools
import time
from typing import Any, Callable, Optional, TypeVar

from prometheus_client import Counter, Gauge, Histogram, Summary

# Define metrics
OPERATION_COUNT = Counter(
    "koocad_operations_total",
    "Total number of operations",
    ["operation_type", "status"],
)

OPERATION_DURATION = Histogram(
    "koocad_operation_duration_seconds",
    "Duration of operations in seconds",
    ["operation_type"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

PARAMETER_COUNT = Gauge(
    "koocad_active_parameters",
    "Number of active parameters in current session",
)

CAD_GENERATION_COUNT = Counter(
    "koocad_cad_generations_total",
    "Total number of CAD models generated",
    ["component_type", "kernel"],
)

CAD_GENERATION_DURATION = Histogram(
    "koocad_cad_generation_duration_seconds",
    "CAD generation duration in seconds",
    ["component_type", "kernel"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

EXPORT_SIZE = Histogram(
    "koocad_export_size_bytes",
    "Size of exported files in bytes",
    ["format"],
    buckets=(1e3, 1e4, 1e5, 1e6, 1e7, 1e8),
)

EXPORT_COUNT = Counter(
    "koocad_exports_total",
    "Total number of file exports",
    ["format", "status"],
)

MESH_ELEMENT_COUNT = Histogram(
    "koocad_mesh_elements",
    "Number of mesh elements generated",
    ["mesh_type"],
    buckets=(100, 1000, 10000, 100000, 1000000),
)

JOB_QUEUE_SIZE = Gauge(
    "koocad_job_queue_size",
    "Number of jobs in queue",
    ["queue_name"],
)

ACTIVE_JOBS = Gauge(
    "koocad_active_jobs",
    "Number of currently running jobs",
)

F = TypeVar("F", bound=Callable[..., Any])


def track_operation(operation_type: str) -> Callable[[F], F]:
    """Decorator to track operation count and duration.

    Args:
        operation_type: Type of operation (e.g., "cad_generation", "export").

    Example:
        >>> @track_operation("parameter_validation")
        ... def validate_parameters(params):
        ...     # validation logic
        ...     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                OPERATION_COUNT.labels(operation_type=operation_type, status=status).inc()
                OPERATION_DURATION.labels(operation_type=operation_type).observe(duration)

        return wrapper  # type: ignore

    return decorator


def track_cad_generation(component_type: str, kernel: str = "cadquery") -> Callable[[F], F]:
    """Decorator to track CAD generation metrics.

    Args:
        component_type: Type of component (e.g., "bga", "mlcc").
        kernel: CAD kernel used (e.g., "cadquery", "occt").

    Example:
        >>> @track_cad_generation("bga", "cadquery")
        ... def generate_bga(params):
        ...     # generation logic
        ...     return shape
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                CAD_GENERATION_COUNT.labels(
                    component_type=component_type, kernel=kernel
                ).inc()
                return result
            finally:
                duration = time.time() - start_time
                CAD_GENERATION_DURATION.labels(
                    component_type=component_type, kernel=kernel
                ).observe(duration)

        return wrapper  # type: ignore

    return decorator


def track_export(file_format: str) -> Callable[[F], F]:
    """Decorator to track export operations.

    Args:
        file_format: Export format (e.g., "step", "stl", "glb").

    Example:
        >>> @track_export("step")
        ... def export_step(shape, path):
        ...     # export logic
        ...     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                EXPORT_COUNT.labels(format=file_format, status=status).inc()

        return wrapper  # type: ignore

    return decorator


class MetricsContext:
    """Context manager for tracking metrics within a block.

    Example:
        >>> with MetricsContext("complex_operation") as ctx:
        ...     # do work
        ...     ctx.set_metadata(items_processed=100)
    """

    def __init__(self, operation_type: str) -> None:
        """Initialize metrics context.

        Args:
            operation_type: Type of operation being tracked.
        """
        self.operation_type = operation_type
        self.start_time: Optional[float] = None
        self.metadata: dict[str, Any] = {}

    def __enter__(self) -> "MetricsContext":
        """Enter context and start timer."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and record metrics."""
        if self.start_time is not None:
            duration = time.time() - self.start_time
            status = "error" if exc_type is not None else "success"

            OPERATION_COUNT.labels(
                operation_type=self.operation_type, status=status
            ).inc()
            OPERATION_DURATION.labels(operation_type=self.operation_type).observe(
                duration
            )

    def set_metadata(self, **kwargs: Any) -> None:
        """Set metadata for this operation."""
        self.metadata.update(kwargs)


# Utility functions for common metric updates
def record_parameter_count(count: int) -> None:
    """Update the active parameter count gauge."""
    PARAMETER_COUNT.set(count)


def record_export_size(file_format: str, size_bytes: int) -> None:
    """Record the size of an exported file."""
    EXPORT_SIZE.labels(format=file_format).observe(size_bytes)


def record_mesh_elements(mesh_type: str, element_count: int) -> None:
    """Record the number of mesh elements generated."""
    MESH_ELEMENT_COUNT.labels(mesh_type=mesh_type).observe(element_count)


def update_queue_size(queue_name: str, size: int) -> None:
    """Update job queue size gauge."""
    JOB_QUEUE_SIZE.labels(queue_name=queue_name).set(size)


def increment_active_jobs() -> None:
    """Increment active job counter."""
    ACTIVE_JOBS.inc()


def decrement_active_jobs() -> None:
    """Decrement active job counter."""
    ACTIVE_JOBS.dec()
