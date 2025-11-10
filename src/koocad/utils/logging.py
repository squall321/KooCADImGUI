"""
Structured logging configuration using structlog.

This module provides JSON-based structured logging with automatic
context injection (request ID, user ID, etc.) for debugging and monitoring.
"""

import logging
import sys
from typing import Any, Optional

import structlog
from structlog.types import EventDict, Processor


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application-specific context to log records."""
    event_dict["app"] = "koocad"
    event_dict["version"] = "0.1.0"
    return event_dict


def add_log_level_name(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add human-readable log level name."""
    if method_name == "warn":
        # structlog uses "warn" but logging uses "warning"
        event_dict["level"] = "WARNING"
    else:
        event_dict["level"] = method_name.upper()
    return event_dict


def setup_logging(
    *,
    log_level: str = "INFO",
    json_format: bool = True,
    include_timestamp: bool = True,
) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, output JSON logs. If False, use human-readable format.
        include_timestamp: Whether to include timestamps in logs.

    Example:
        >>> setup_logging(log_level="DEBUG", json_format=True)
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started", user_id=123)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Build processor chain
    processors: list[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        add_log_level_name,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso") if include_timestamp else lambda _, __, ed: ed,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add renderer based on format
    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a logger instance for the given name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        Configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", job_id="12345")
    """
    return structlog.get_logger(name)


class LogContext:
    """Context manager for adding temporary logging context.

    Example:
        >>> logger = get_logger(__name__)
        >>> with LogContext(request_id="abc123"):
        ...     logger.info("Processing request")
        # Output includes request_id="abc123"
    """

    def __init__(self, **context: Any) -> None:
        """Initialize context manager with key-value pairs."""
        self.context = context
        self.token: Optional[Any] = None

    def __enter__(self) -> None:
        """Enter context and bind variables."""
        self.token = structlog.contextvars.bind_contextvars(**self.context)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and unbind variables."""
        structlog.contextvars.unbind_contextvars(*self.context.keys())


# Convenience functions for common log levels
def debug(message: str, **kwargs: Any) -> None:
    """Log a debug message."""
    logger = get_logger("koocad")
    logger.debug(message, **kwargs)


def info(message: str, **kwargs: Any) -> None:
    """Log an info message."""
    logger = get_logger("koocad")
    logger.info(message, **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """Log a warning message."""
    logger = get_logger("koocad")
    logger.warning(message, **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """Log an error message."""
    logger = get_logger("koocad")
    logger.error(message, **kwargs)


def critical(message: str, **kwargs: Any) -> None:
    """Log a critical message."""
    logger = get_logger("koocad")
    logger.critical(message, **kwargs)
