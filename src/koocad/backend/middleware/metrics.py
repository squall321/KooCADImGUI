"""
Prometheus metrics collection middleware.

Metrics collected:
- HTTP request duration
- Request count by method/path/status
- Active requests
- Error rate
"""

from __future__ import annotations

import time
from typing import Callable

try:
    from fastapi import Request, Response
    from starlette.middleware.base import BaseHTTPMiddleware
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Request = None  # type: ignore
    Response = None  # type: ignore
    BaseHTTPMiddleware = None  # type: ignore
    Counter = None  # type: ignore
    Histogram = None  # type: ignore
    Gauge = None  # type: ignore


if PROMETHEUS_AVAILABLE:
    # Define metrics
    REQUEST_COUNT = Counter(
        "koocad_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )

    REQUEST_DURATION = Histogram(
        "koocad_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ["method", "endpoint"],
        buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

    ACTIVE_REQUESTS = Gauge(
        "koocad_http_requests_active",
        "Number of active HTTP requests",
    )

    ERROR_COUNT = Counter(
        "koocad_http_errors_total",
        "Total HTTP errors (4xx and 5xx)",
        ["method", "endpoint", "status_code"],
    )

    # Job metrics
    JOB_COUNT = Counter(
        "koocad_jobs_total",
        "Total jobs submitted",
        ["job_type", "status"],
    )

    JOB_DURATION = Histogram(
        "koocad_job_duration_seconds",
        "Job execution duration in seconds",
        ["job_type"],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0),
    )

    ACTIVE_JOBS = Gauge(
        "koocad_jobs_active",
        "Number of active jobs",
        ["job_type"],
    )


if PROMETHEUS_AVAILABLE:

    class MetricsMiddleware(BaseHTTPMiddleware):
        """Prometheus metrics collection middleware."""

        async def dispatch(
            self, request: Request, call_next: Callable
        ) -> Response:
            """Process request and collect metrics.

            Args:
                request: HTTP request.
                call_next: Next middleware/handler.

            Returns:
                HTTP response.
            """
            # Track active requests
            ACTIVE_REQUESTS.inc()

            # Record start time
            start_time = time.time()

            try:
                # Process request
                response = await call_next(request)

                # Record metrics
                duration = time.time() - start_time
                endpoint = self._get_endpoint(request)

                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                ).inc()

                REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=endpoint,
                ).observe(duration)

                # Track errors
                if response.status_code >= 400:
                    ERROR_COUNT.labels(
                        method=request.method,
                        endpoint=endpoint,
                        status_code=response.status_code,
                    ).inc()

                return response

            finally:
                # Decrement active requests
                ACTIVE_REQUESTS.dec()

        def _get_endpoint(self, request: Request) -> str:
            """Get endpoint path for metrics.

            Args:
                request: HTTP request.

            Returns:
                Endpoint path (with IDs replaced by {id}).
            """
            path = request.url.path

            # Replace numeric IDs with {id} for better metric grouping
            parts = path.split("/")
            normalized_parts = []
            for part in parts:
                if part.isdigit():
                    normalized_parts.append("{id}")
                else:
                    normalized_parts.append(part)

            return "/".join(normalized_parts)

else:

    class MetricsMiddleware:
        """Placeholder when Prometheus not available."""

        async def dispatch(self, request, call_next):
            """Pass through."""
            return await call_next(request)


def get_metrics() -> tuple[bytes, str]:
    """Get Prometheus metrics.

    Returns:
        Tuple of (metrics_data, content_type).
    """
    if not PROMETHEUS_AVAILABLE:
        return b"", "text/plain"

    return generate_latest(), CONTENT_TYPE_LATEST
