"""
OpenTelemetry distributed tracing integration.

This module provides decorators and utilities for adding distributed tracing
to CAD operations for performance analysis and debugging.
"""

import functools
from typing import Any, Callable, Optional, TypeVar

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

# Global tracer
_tracer: Optional[trace.Tracer] = None


def setup_tracing(
    service_name: str = "koocad",
    otlp_endpoint: Optional[str] = None,
    enable: bool = True,
) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        service_name: Name of the service for trace identification.
        otlp_endpoint: OTLP collector endpoint (e.g., "localhost:4317").
        enable: Whether to enable tracing.

    Example:
        >>> setup_tracing(service_name="koocad", otlp_endpoint="localhost:4317")
    """
    global _tracer

    if not enable:
        _tracer = trace.get_tracer(__name__)
        return

    # Create resource with service name
    resource = Resource.create({"service.name": service_name})

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter if endpoint provided
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer instance
    _tracer = trace.get_tracer(__name__)


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance.

    Returns:
        Configured tracer.

    Raises:
        RuntimeError: If tracing not initialized.
    """
    if _tracer is None:
        # Auto-initialize with defaults
        setup_tracing(enable=False)

    assert _tracer is not None
    return _tracer


F = TypeVar("F", bound=Callable[..., Any])


def trace_operation(
    operation_name: Optional[str] = None,
    *,
    capture_args: bool = False,
    capture_result: bool = False,
) -> Callable[[F], F]:
    """Decorator to trace a function execution.

    Args:
        operation_name: Name for the span (defaults to function name).
        capture_args: Whether to capture function arguments as span attributes.
        capture_result: Whether to capture return value as span attribute.

    Example:
        >>> @trace_operation("generate_bga", capture_args=True)
        ... def generate_bga(width, height):
        ...     return create_shape(width, height)
    """

    def decorator(func: F) -> F:
        span_name = operation_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracer = get_tracer()

            with tracer.start_as_current_span(span_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)

                # Capture arguments if requested
                if capture_args:
                    # Capture positional args
                    for i, arg in enumerate(args):
                        span.set_attribute(f"arg.{i}", str(arg))

                    # Capture keyword args
                    for key, value in kwargs.items():
                        span.set_attribute(f"kwarg.{key}", str(value))

                try:
                    result = func(*args, **kwargs)

                    # Capture result if requested
                    if capture_result and result is not None:
                        span.set_attribute("result", str(result)[:200])  # Truncate

                    span.set_status(Status(StatusCode.OK))
                    return result

                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        return wrapper  # type: ignore

    return decorator


class TracingContext:
    """Context manager for manual span creation.

    Example:
        >>> with TracingContext("complex_operation") as span:
        ...     span.add_event("Starting phase 1")
        ...     # do work
        ...     span.set_attribute("items_processed", 100)
    """

    def __init__(self, span_name: str, **attributes: Any) -> None:
        """Initialize tracing context.

        Args:
            span_name: Name for the span.
            **attributes: Initial span attributes.
        """
        self.span_name = span_name
        self.attributes = attributes
        self.span: Optional[trace.Span] = None

    def __enter__(self) -> trace.Span:
        """Enter context and start span."""
        tracer = get_tracer()
        self.span = tracer.start_span(self.span_name)

        # Set initial attributes
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)

        return self.span

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and end span."""
        if self.span is not None:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))

            self.span.end()


def add_span_attribute(key: str, value: Any) -> None:
    """Add an attribute to the current span.

    Args:
        key: Attribute key.
        value: Attribute value.

    Example:
        >>> add_span_attribute("component_type", "bga")
    """
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.set_attribute(key, value)


def add_span_event(name: str, **attributes: Any) -> None:
    """Add an event to the current span.

    Args:
        name: Event name.
        **attributes: Event attributes.

    Example:
        >>> add_span_event("parameter_validated", param_count=15)
    """
    current_span = trace.get_current_span()
    if current_span.is_recording():
        current_span.add_event(name, attributes=attributes)


# Convenience decorators for common operations
def trace_cad_generation(func: F) -> F:
    """Trace CAD generation operations."""
    return trace_operation("cad_generation", capture_args=True)(func)


def trace_export(func: F) -> F:
    """Trace export operations."""
    return trace_operation("export", capture_args=True)(func)


def trace_parameter_validation(func: F) -> F:
    """Trace parameter validation operations."""
    return trace_operation("parameter_validation")(func)


def trace_mesh_generation(func: F) -> F:
    """Trace mesh generation operations."""
    return trace_operation("mesh_generation", capture_args=True)(func)
