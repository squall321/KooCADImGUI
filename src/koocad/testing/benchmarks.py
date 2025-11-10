"""
Performance benchmarking utilities.

This module provides decorators and utilities for benchmarking CAD operations
using pytest-benchmark.
"""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar

import psutil

F = TypeVar("F", bound=Callable[..., Any])


class PerformanceMetrics:
    """Container for performance metrics."""

    def __init__(self) -> None:
        """Initialize metrics container."""
        self.duration: float = 0.0
        self.memory_used: int = 0  # bytes
        self.cpu_percent: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def __repr__(self) -> str:
        """String representation of metrics."""
        return (
            f"PerformanceMetrics(duration={self.duration:.3f}s, "
            f"memory={self.memory_used / 1024 / 1024:.2f}MB, "
            f"cpu={self.cpu_percent:.1f}%)"
        )


def measure_performance(func: F) -> F:
    """Decorator to measure function performance.

    Measures execution time, memory usage, and CPU utilization.

    Args:
        func: Function to measure.

    Returns:
        Wrapped function that returns (result, metrics).

    Example:
        >>> @measure_performance
        ... def generate_model(params):
        ...     return create_shape(params)
        >>> result, metrics = generate_model(params)
        >>> print(metrics.duration)
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> tuple[Any, PerformanceMetrics]:
        metrics = PerformanceMetrics()

        # Get process for memory tracking
        process = psutil.Process()

        # Measure initial state
        mem_before = process.memory_info().rss
        cpu_before = process.cpu_percent(interval=0.1)

        # Execute function
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        # Measure final state
        mem_after = process.memory_info().rss
        cpu_after = process.cpu_percent(interval=0.1)

        # Record metrics
        metrics.duration = duration
        metrics.memory_used = mem_after - mem_before
        metrics.cpu_percent = (cpu_before + cpu_after) / 2

        return result, metrics

    return wrapper  # type: ignore


class BenchmarkContext:
    """Context manager for manual performance measurement.

    Example:
        >>> with BenchmarkContext("cad_generation") as bench:
        ...     # do work
        ...     pass
        >>> print(bench.metrics.duration)
    """

    def __init__(self, operation_name: str) -> None:
        """Initialize benchmark context.

        Args:
            operation_name: Name of operation being benchmarked.
        """
        self.operation_name = operation_name
        self.metrics = PerformanceMetrics()
        self.start_time: Optional[float] = None
        self.process = psutil.Process()
        self.mem_before: int = 0

    def __enter__(self) -> "BenchmarkContext":
        """Enter context and start measurement."""
        self.mem_before = self.process.memory_info().rss
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and record metrics."""
        if self.start_time is not None:
            self.metrics.duration = time.time() - self.start_time
            mem_after = self.process.memory_info().rss
            self.metrics.memory_used = mem_after - self.mem_before
            self.metrics.cpu_percent = self.process.cpu_percent(interval=0.1)


# Benchmark targets for common operations
class CADBenchmarks:
    """Collection of CAD operation benchmarks."""

    @staticmethod
    def benchmark_box_creation(width: float, height: float, depth: float) -> PerformanceMetrics:
        """Benchmark simple box creation.

        Args:
            width: Box width.
            height: Box height.
            depth: Box depth.

        Returns:
            Performance metrics.
        """
        from koocad.testing.benchmarks import measure_performance

        @measure_performance
        def create_box() -> Any:
            # Placeholder - will be implemented when CAD kernel is ready
            time.sleep(0.001)  # Simulate operation
            return {"type": "box", "volume": width * height * depth}

        _, metrics = create_box()
        return metrics

    @staticmethod
    def benchmark_boolean_union(shape_count: int) -> PerformanceMetrics:
        """Benchmark boolean union of multiple shapes.

        Args:
            shape_count: Number of shapes to union.

        Returns:
            Performance metrics.
        """

        @measure_performance
        def perform_union() -> Any:
            # Placeholder
            time.sleep(0.01 * shape_count)
            return {"type": "union", "count": shape_count}

        _, metrics = perform_union()
        return metrics

    @staticmethod
    def benchmark_parameter_evaluation(param_count: int) -> PerformanceMetrics:
        """Benchmark parameter set evaluation.

        Args:
            param_count: Number of parameters to evaluate.

        Returns:
            Performance metrics.
        """
        from koocad.testing.factories import ParameterFactory
        from koocad.core.parameters import ParameterSet

        @measure_performance
        def evaluate_params() -> Any:
            param_set = ParameterSet()
            for i in range(param_count):
                param = ParameterFactory.create_float(name=f"param_{i}")
                param_set.add(param)
            return param_set.evaluate_all()

        _, metrics = evaluate_params()
        return metrics


class BenchmarkReporter:
    """Generate benchmark reports."""

    @staticmethod
    def compare_results(
        baseline: PerformanceMetrics,
        current: PerformanceMetrics,
    ) -> Dict[str, Any]:
        """Compare two benchmark results.

        Args:
            baseline: Baseline metrics.
            current: Current metrics.

        Returns:
            Dictionary with comparison statistics.

        Example:
            >>> report = BenchmarkReporter.compare_results(baseline, current)
            >>> print(f"Speed change: {report['duration_change_percent']:.1f}%")
        """
        duration_change = (
            (current.duration - baseline.duration) / baseline.duration * 100
        )
        memory_change = (
            (current.memory_used - baseline.memory_used) / baseline.memory_used * 100
            if baseline.memory_used > 0
            else 0
        )

        return {
            "duration_change_percent": duration_change,
            "memory_change_percent": memory_change,
            "duration_regression": duration_change > 10,  # >10% slower
            "memory_regression": memory_change > 20,  # >20% more memory
            "baseline_duration": baseline.duration,
            "current_duration": current.duration,
            "baseline_memory_mb": baseline.memory_used / 1024 / 1024,
            "current_memory_mb": current.memory_used / 1024 / 1024,
        }

    @staticmethod
    def format_report(comparison: Dict[str, Any]) -> str:
        """Format comparison results as human-readable string.

        Args:
            comparison: Comparison dictionary from compare_results.

        Returns:
            Formatted report string.
        """
        lines = [
            "Performance Comparison Report",
            "=" * 40,
            f"Duration: {comparison['baseline_duration']:.3f}s → "
            f"{comparison['current_duration']:.3f}s "
            f"({comparison['duration_change_percent']:+.1f}%)",
            f"Memory: {comparison['baseline_memory_mb']:.2f}MB → "
            f"{comparison['current_memory_mb']:.2f}MB "
            f"({comparison['memory_change_percent']:+.1f}%)",
            "",
            "Regressions:",
        ]

        if comparison["duration_regression"]:
            lines.append("  ⚠️  Duration regression detected!")
        if comparison["memory_regression"]:
            lines.append("  ⚠️  Memory regression detected!")

        if not (comparison["duration_regression"] or comparison["memory_regression"]):
            lines.append("  ✓ No regressions detected")

        return "\n".join(lines)
