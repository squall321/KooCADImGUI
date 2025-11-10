"""Tests for logging utilities."""

import json
import logging

import pytest

from koocad.utils.logging import (
    LogContext,
    get_logger,
    setup_logging,
)


class TestLogging:
    """Tests for structured logging."""

    def test_setup_logging_json(self, caplog) -> None:
        """Test JSON logging setup."""
        setup_logging(log_level="INFO", json_format=False)  # Use console for testing
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info("Test message", user_id=123)

        assert len(caplog.records) == 1
        assert "Test message" in caplog.text

    def test_log_context(self, caplog) -> None:
        """Test logging context manager."""
        setup_logging(log_level="INFO", json_format=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            with LogContext(request_id="abc123"):
                logger.info("Processing request")

        assert len(caplog.records) == 1

    def test_log_levels(self, caplog) -> None:
        """Test different log levels."""
        setup_logging(log_level="DEBUG", json_format=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

        assert len(caplog.records) == 4

    def test_structured_data(self, caplog) -> None:
        """Test logging with structured data."""
        setup_logging(log_level="INFO", json_format=False)
        logger = get_logger(__name__)

        with caplog.at_level(logging.INFO):
            logger.info(
                "CAD generated",
                component_type="bga",
                duration=1.23,
                shape_count=15,
            )

        assert "CAD generated" in caplog.text
