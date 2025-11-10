"""
Performance profiler for expression evaluation.

This module provides tools to profile parameter expression evaluation
and identify performance bottlenecks.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table

from koocad.core.parameters import ExpressionParameter, ParameterSet


@dataclass
class ProfileResult:
    """Result of profiling a parameter evaluation."""

    param_name: str
    evaluation_time: float  # seconds
    value: float
    dependencies_count: int
    error: Optional[str] = None


@dataclass
class ProfilingSession:
    """Session containing multiple profile results."""

    results: List[ProfileResult] = field(default_factory=list)
    total_time: float = 0.0

    def add_result(self, result: ProfileResult) -> None:
        """Add result to session."""
        self.results.append(result)
        self.total_time += result.evaluation_time

    def get_slowest(self, n: int = 10) -> List[ProfileResult]:
        """Get N slowest evaluations."""
        return sorted(self.results, key=lambda r: r.evaluation_time, reverse=True)[:n]

    def get_failed(self) -> List[ProfileResult]:
        """Get failed evaluations."""
        return [r for r in self.results if r.error is not None]

    def get_summary(self) -> Dict[str, any]:
        """Get summary statistics."""
        if not self.results:
            return {}

        times = [r.evaluation_time for r in self.results]

        return {
            "total_parameters": len(self.results),
            "total_time": self.total_time,
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "failed_count": len(self.get_failed()),
        }


class ExpressionProfiler:
    """Profiler for expression evaluation performance."""

    def __init__(self, param_set: ParameterSet) -> None:
        """Initialize profiler.

        Args:
            param_set: ParameterSet to profile.
        """
        self.param_set = param_set
        self.console = Console()

    def profile_parameter(self, param_name: str, iterations: int = 100) -> ProfileResult:
        """Profile single parameter evaluation.

        Args:
            param_name: Parameter name to profile.
            iterations: Number of iterations for timing.

        Returns:
            Profile result.
        """
        param = self.param_set.get(param_name)

        if param is None:
            return ProfileResult(
                param_name=param_name,
                evaluation_time=0.0,
                value=0.0,
                dependencies_count=0,
                error=f"Parameter '{param_name}' not found",
            )

        if not isinstance(param, ExpressionParameter):
            return ProfileResult(
                param_name=param_name,
                evaluation_time=0.0,
                value=param.value,
                dependencies_count=0,
                error="Not an expression parameter",
            )

        # Get evaluation context
        try:
            context = self.param_set.evaluate_all()
        except Exception as e:
            return ProfileResult(
                param_name=param_name,
                evaluation_time=0.0,
                value=0.0,
                dependencies_count=len(param.dependencies),
                error=f"Failed to evaluate context: {e}",
            )

        # Time evaluation
        start = time.perf_counter()

        try:
            for _ in range(iterations):
                value = param.evaluate(context)
            elapsed = time.perf_counter() - start

            return ProfileResult(
                param_name=param_name,
                evaluation_time=elapsed / iterations,  # Average time per iteration
                value=value,
                dependencies_count=len(param.dependencies),
            )

        except Exception as e:
            elapsed = time.perf_counter() - start
            return ProfileResult(
                param_name=param_name,
                evaluation_time=elapsed / iterations,
                value=0.0,
                dependencies_count=len(param.dependencies),
                error=str(e),
            )

    def profile_all(self, iterations: int = 100) -> ProfilingSession:
        """Profile all expression parameters.

        Args:
            iterations: Number of iterations for timing.

        Returns:
            Profiling session with all results.
        """
        session = ProfilingSession()

        for name, param in self.param_set.parameters.items():
            if isinstance(param, ExpressionParameter):
                result = self.profile_parameter(name, iterations=iterations)
                session.add_result(result)

        return session

    def print_session(self, session: ProfilingSession, top_n: int = 10) -> None:
        """Print profiling session results.

        Args:
            session: Profiling session to print.
            top_n: Number of slowest parameters to show.
        """
        summary = session.get_summary()

        # Summary table
        self.console.print("\n[bold]Profiling Summary[/bold]")
        summary_table = Table()
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")

        summary_table.add_row("Total Parameters", str(summary.get("total_parameters", 0)))
        summary_table.add_row("Total Time", f"{summary.get('total_time', 0):.6f} s")
        summary_table.add_row("Average Time", f"{summary.get('average_time', 0):.6f} s")
        summary_table.add_row("Min Time", f"{summary.get('min_time', 0):.6f} s")
        summary_table.add_row("Max Time", f"{summary.get('max_time', 0):.6f} s")
        summary_table.add_row("Failed Count", str(summary.get("failed_count", 0)))

        self.console.print(summary_table)

        # Slowest parameters
        slowest = session.get_slowest(top_n)
        if slowest:
            self.console.print(f"\n[bold]Top {len(slowest)} Slowest Parameters[/bold]")
            slowest_table = Table()
            slowest_table.add_column("Rank", style="dim")
            slowest_table.add_column("Parameter", style="cyan")
            slowest_table.add_column("Time (s)", style="yellow")
            slowest_table.add_column("Dependencies", style="blue")
            slowest_table.add_column("Value", style="green")

            for i, result in enumerate(slowest, 1):
                slowest_table.add_row(
                    str(i),
                    result.param_name,
                    f"{result.evaluation_time:.6f}",
                    str(result.dependencies_count),
                    f"{result.value:.2f}",
                )

            self.console.print(slowest_table)

        # Failed evaluations
        failed = session.get_failed()
        if failed:
            self.console.print(f"\n[red]⚠ Failed Evaluations ({len(failed)})[/red]")
            failed_table = Table()
            failed_table.add_column("Parameter", style="cyan")
            failed_table.add_column("Error", style="red")

            for result in failed:
                failed_table.add_row(result.param_name, result.error or "Unknown error")

            self.console.print(failed_table)

    def benchmark_scaling(self, param_name: str, max_iterations: int = 10000) -> Dict[int, float]:
        """Benchmark parameter evaluation scaling.

        Args:
            param_name: Parameter to benchmark.
            max_iterations: Maximum iterations to test.

        Returns:
            Dictionary mapping iteration counts to times.
        """
        param = self.param_set.get(param_name)

        if param is None or not isinstance(param, ExpressionParameter):
            return {}

        context = self.param_set.evaluate_all()
        results = {}

        # Test with increasing iteration counts
        for iterations in [10, 100, 1000, 10000, max_iterations]:
            if iterations > max_iterations:
                break

            start = time.perf_counter()
            for _ in range(iterations):
                param.evaluate(context)
            elapsed = time.perf_counter() - start

            results[iterations] = elapsed

        return results

    def find_bottlenecks(self, threshold_ms: float = 1.0) -> List[str]:
        """Find parameters that take longer than threshold to evaluate.

        Args:
            threshold_ms: Threshold in milliseconds.

        Returns:
            List of parameter names that exceed threshold.
        """
        session = self.profile_all(iterations=100)
        threshold_s = threshold_ms / 1000.0

        bottlenecks = [result.param_name for result in session.results if result.evaluation_time > threshold_s]

        return bottlenecks

    def optimize_suggestions(self, session: ProfilingSession) -> List[str]:
        """Generate optimization suggestions based on profiling results.

        Args:
            session: Profiling session.

        Returns:
            List of optimization suggestions.
        """
        suggestions = []

        # Check for slow parameters
        slowest = session.get_slowest(5)
        if slowest:
            suggestions.append(
                f"Consider caching results for slowest parameters: {', '.join(r.param_name for r in slowest[:3])}"
            )

        # Check for parameters with many dependencies
        complex_params = [r for r in session.results if r.dependencies_count > 10]
        if complex_params:
            suggestions.append(
                f"Parameters with many dependencies may benefit from simplification: "
                f"{', '.join(r.param_name for r in complex_params[:3])}"
            )

        # Check for failed evaluations
        failed = session.get_failed()
        if failed:
            suggestions.append(f"Fix evaluation errors in: {', '.join(r.param_name for r in failed[:3])}")

        # Check for total time
        summary = session.get_summary()
        if summary.get("total_time", 0) > 1.0:
            suggestions.append("Consider using compiled expressions or caching for better performance")

        return suggestions

    def print_optimization_suggestions(self, session: ProfilingSession) -> None:
        """Print optimization suggestions.

        Args:
            session: Profiling session.
        """
        suggestions = self.optimize_suggestions(session)

        if suggestions:
            self.console.print("\n[bold]Optimization Suggestions[/bold]")
            for i, suggestion in enumerate(suggestions, 1):
                self.console.print(f"{i}. {suggestion}")
        else:
            self.console.print("\n[green]✓ No obvious bottlenecks detected[/green]")
