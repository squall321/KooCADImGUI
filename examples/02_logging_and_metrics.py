"""
Example 2: Logging and Metrics

This example demonstrates structured logging and Prometheus metrics collection.
"""

import time

from prometheus_client import start_http_server

from koocad.utils.logging import LogContext, get_logger, setup_logging
from koocad.utils.metrics import (
    MetricsContext,
    record_parameter_count,
    track_cad_generation,
    track_operation,
)


def main() -> None:
    """Run logging and metrics examples."""
    # Setup structured logging
    setup_logging(log_level="INFO", json_format=False)
    logger = get_logger(__name__)

    print("=" * 60)
    print("KooCAD - Logging and Metrics Demo")
    print("=" * 60)

    # Example 1: Basic logging
    print("\n1. Basic Structured Logging")
    print("-" * 40)

    logger.info("Application started", version="0.1.0")
    logger.debug("Debug information", config_loaded=True)
    logger.warning("This is a warning", retry_count=3)

    # Example 2: Logging with context
    print("\n2. Logging with Context")
    print("-" * 40)

    with LogContext(request_id="req_12345", user_id="user_789"):
        logger.info("Processing user request")
        logger.info("Operation completed")

    # Example 3: Metrics tracking with decorator
    print("\n3. Metrics Tracking with Decorator")
    print("-" * 40)

    @track_operation("parameter_validation")
    def validate_parameters(count: int) -> dict:
        """Simulate parameter validation."""
        time.sleep(0.1)  # Simulate work
        return {"validated": count, "errors": 0}

    result = validate_parameters(15)
    logger.info("Parameters validated", result=result)

    # Example 4: CAD generation metrics
    print("\n4. CAD Generation Metrics")
    print("-" * 40)

    @track_cad_generation("bga", "cadquery")
    def generate_bga_model() -> dict:
        """Simulate BGA generation."""
        time.sleep(0.5)  # Simulate CAD generation
        return {"vertices": 1234, "faces": 2468}

    shape_info = generate_bga_model()
    logger.info("BGA model generated", shape_info=shape_info)

    # Example 5: Manual metrics context
    print("\n5. Manual Metrics Context")
    print("-" * 40)

    with MetricsContext("complex_operation") as ctx:
        logger.info("Starting complex operation")

        # Simulate work
        time.sleep(0.2)

        ctx.set_metadata(items_processed=100, cache_hits=75)
        logger.info("Complex operation completed")

    # Example 6: Gauge metrics
    print("\n6. Gauge Metrics (Parameter Count)")
    print("-" * 40)

    record_parameter_count(25)
    logger.info("Active parameters updated", count=25)

    # Example 7: Start Prometheus metrics server
    print("\n7. Prometheus Metrics Server")
    print("-" * 40)

    try:
        start_http_server(8001)
        print("✓ Prometheus metrics available at http://localhost:8001/metrics")
        print("  - koocad_operations_total")
        print("  - koocad_operation_duration_seconds")
        print("  - koocad_cad_generations_total")
        print("  - koocad_active_parameters")
    except OSError:
        print("⚠ Port 8001 already in use (metrics server may be running)")

    print("\n" + "=" * 60)
    print("Demo completed!")
    print("=" * 60)
    print("\nView metrics:")
    print("  curl http://localhost:8001/metrics")


if __name__ == "__main__":
    main()
