"""
Result aggregation and analysis.

Features:
- Collect results from parameter sweep jobs
- Compute summary statistics
- Generate plots and visualizations
- Export aggregated data
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import statistics


class ResultAggregator:
    """Result collection and aggregation tool."""

    def __init__(self):
        """Initialize result aggregator."""
        self.results: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def add_result(
        self,
        job_id: int,
        parameters: Dict[str, Any],
        outputs: Dict[str, Any],
        status: str = "SUCCESS",
        error: Optional[str] = None,
    ) -> None:
        """Add job result.

        Args:
            job_id: Job ID.
            parameters: Input parameters.
            outputs: Output metrics/values.
            status: Job status (SUCCESS, FAILED).
            error: Error message if failed.
        """
        result = {
            "job_id": job_id,
            "parameters": parameters,
            "outputs": outputs,
            "status": status,
            "error": error,
        }
        self.results.append(result)

    def collect_from_directory(
        self,
        directory: str | Path,
        pattern: str = "result_*.json",
    ) -> int:
        """Collect results from directory.

        Args:
            directory: Directory containing result files.
            pattern: Filename pattern to match.

        Returns:
            Number of results collected.
        """
        directory = Path(directory)

        if not directory.exists():
            return 0

        count = 0
        for result_file in directory.glob(pattern):
            try:
                with open(result_file, "r") as f:
                    result = json.load(f)
                    self.results.append(result)
                    count += 1
            except Exception as e:
                print(f"Error loading {result_file}: {e}")

        return count

    def filter_successful(self) -> List[Dict[str, Any]]:
        """Get only successful results.

        Returns:
            List of successful results.
        """
        return [r for r in self.results if r.get("status") == "SUCCESS"]

    def filter_failed(self) -> List[Dict[str, Any]]:
        """Get only failed results.

        Returns:
            List of failed results.
        """
        return [r for r in self.results if r.get("status") != "SUCCESS"]

    def compute_statistics(
        self,
        output_key: str,
    ) -> Dict[str, float]:
        """Compute statistics for output variable.

        Args:
            output_key: Output variable name.

        Returns:
            Statistics dictionary.
        """
        successful = self.filter_successful()
        values = []

        for result in successful:
            outputs = result.get("outputs", {})
            if output_key in outputs:
                try:
                    value = float(outputs[output_key])
                    values.append(value)
                except (ValueError, TypeError):
                    pass

        if not values:
            return {}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
        }

    def find_optimal(
        self,
        output_key: str,
        minimize: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Find optimal result.

        Args:
            output_key: Output variable to optimize.
            minimize: If True, find minimum; if False, find maximum.

        Returns:
            Optimal result, or None if no results.
        """
        successful = self.filter_successful()

        if not successful:
            return None

        best_result = None
        best_value = None

        for result in successful:
            outputs = result.get("outputs", {})
            if output_key not in outputs:
                continue

            try:
                value = float(outputs[output_key])

                if best_value is None:
                    best_value = value
                    best_result = result
                elif minimize and value < best_value:
                    best_value = value
                    best_result = result
                elif not minimize and value > best_value:
                    best_value = value
                    best_result = result

            except (ValueError, TypeError):
                pass

        return best_result

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary report.

        Returns:
            Summary dictionary.
        """
        successful = self.filter_successful()
        failed = self.filter_failed()

        # Collect all output keys
        output_keys = set()
        for result in successful:
            output_keys.update(result.get("outputs", {}).keys())

        # Compute statistics for each output
        output_stats = {}
        for key in output_keys:
            output_stats[key] = self.compute_statistics(key)

        return {
            "total_jobs": len(self.results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(self.results) if self.results else 0.0,
            "output_statistics": output_stats,
        }

    def export_csv(
        self,
        filepath: str | Path,
    ) -> Path:
        """Export results to CSV.

        Args:
            filepath: Output CSV file path.

        Returns:
            Path to exported file.
        """
        import csv

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .csv extension
        if filepath.suffix != ".csv":
            filepath = filepath.with_suffix(".csv")

        # Collect all parameter and output keys
        param_keys = set()
        output_keys = set()

        for result in self.results:
            param_keys.update(result.get("parameters", {}).keys())
            output_keys.update(result.get("outputs", {}).keys())

        # Write CSV
        with open(filepath, "w", newline="") as f:
            fieldnames = ["job_id", "status"] + sorted(param_keys) + sorted(output_keys)
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

            for result in self.results:
                row = {
                    "job_id": result.get("job_id"),
                    "status": result.get("status"),
                }
                row.update(result.get("parameters", {}))
                row.update(result.get("outputs", {}))

                writer.writerow(row)

        return filepath

    def export_json(
        self,
        filepath: str | Path,
    ) -> Path:
        """Export results to JSON.

        Args:
            filepath: Output JSON file path.

        Returns:
            Path to exported file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "summary": self.generate_summary(),
            "results": self.results,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def plot_1d(
        self,
        param_key: str,
        output_key: str,
        filepath: str | Path,
    ) -> Optional[Path]:
        """Generate 1D plot.

        Args:
            param_key: Parameter name (x-axis).
            output_key: Output name (y-axis).
            filepath: Output plot file path.

        Returns:
            Path to plot file, or None if matplotlib not available.
        """
        try:
            import matplotlib.pyplot as plt

            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Extract data
            x_values = []
            y_values = []

            for result in self.filter_successful():
                params = result.get("parameters", {})
                outputs = result.get("outputs", {})

                if param_key in params and output_key in outputs:
                    try:
                        x = float(params[param_key])
                        y = float(outputs[output_key])
                        x_values.append(x)
                        y_values.append(y)
                    except (ValueError, TypeError):
                        pass

            if not x_values:
                return None

            # Create plot
            plt.figure(figsize=(10, 6))
            plt.scatter(x_values, y_values, alpha=0.6)
            plt.xlabel(param_key)
            plt.ylabel(output_key)
            plt.title(f"{output_key} vs {param_key}")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(filepath, dpi=150)
            plt.close()

            return filepath

        except ImportError:
            print("Warning: matplotlib not installed")
            return None

    def plot_2d(
        self,
        param_x: str,
        param_y: str,
        output_key: str,
        filepath: str | Path,
    ) -> Optional[Path]:
        """Generate 2D contour plot.

        Args:
            param_x: First parameter (x-axis).
            param_y: Second parameter (y-axis).
            output_key: Output for color.
            filepath: Output plot file path.

        Returns:
            Path to plot file, or None if matplotlib not available.
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Extract data
            x_values = []
            y_values = []
            z_values = []

            for result in self.filter_successful():
                params = result.get("parameters", {})
                outputs = result.get("outputs", {})

                if param_x in params and param_y in params and output_key in outputs:
                    try:
                        x = float(params[param_x])
                        y = float(params[param_y])
                        z = float(outputs[output_key])
                        x_values.append(x)
                        y_values.append(y)
                        z_values.append(z)
                    except (ValueError, TypeError):
                        pass

            if not x_values:
                return None

            # Create scatter plot with color
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(x_values, y_values, c=z_values, cmap="viridis", alpha=0.6, s=50)
            plt.colorbar(scatter, label=output_key)
            plt.xlabel(param_x)
            plt.ylabel(param_y)
            plt.title(f"{output_key} vs ({param_x}, {param_y})")
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(filepath, dpi=150)
            plt.close()

            return filepath

        except ImportError:
            print("Warning: matplotlib not installed")
            return None
