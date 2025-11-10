"""
Parameter sweep generator for Design of Experiments (DoE).

Sampling strategies:
- Cartesian product: Full factorial design
- Random sampling: Monte Carlo
- Sobol sequence: Quasi-Monte Carlo (QMC)
- Latin Hypercube: Space-filling design
"""

from __future__ import annotations

import itertools
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ParameterSweep:
    """Parameter sweep generator for DoE."""

    def __init__(self):
        """Initialize parameter sweep."""
        self.parameters: Dict[str, List[Any]] = {}
        self.samples: List[Dict[str, Any]] = []

    def add_parameter(
        self,
        name: str,
        values: List[Any],
    ) -> None:
        """Add parameter with discrete values.

        Args:
            name: Parameter name.
            values: List of parameter values.
        """
        self.parameters[name] = values

    def add_range(
        self,
        name: str,
        min_val: float,
        max_val: float,
        count: int,
    ) -> None:
        """Add parameter with continuous range.

        Args:
            name: Parameter name.
            min_val: Minimum value.
            max_val: Maximum value.
            count: Number of samples.
        """
        step = (max_val - min_val) / (count - 1) if count > 1 else 0
        values = [min_val + i * step for i in range(count)]
        self.parameters[name] = values

    def generate_cartesian(self) -> List[Dict[str, Any]]:
        """Generate full factorial (Cartesian product) design.

        Returns:
            List of parameter combinations.
        """
        if not self.parameters:
            return []

        # Get all parameter names and values
        names = list(self.parameters.keys())
        value_lists = [self.parameters[name] for name in names]

        # Cartesian product
        self.samples = []
        for combination in itertools.product(*value_lists):
            sample = dict(zip(names, combination))
            self.samples.append(sample)

        return self.samples

    def generate_random(
        self,
        n_samples: int,
        seed: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Generate random samples (Monte Carlo).

        Args:
            n_samples: Number of samples.
            seed: Random seed for reproducibility.

        Returns:
            List of parameter combinations.
        """
        if seed is not None:
            random.seed(seed)

        self.samples = []
        for _ in range(n_samples):
            sample = {}
            for name, values in self.parameters.items():
                sample[name] = random.choice(values)
            self.samples.append(sample)

        return self.samples

    def generate_sobol(
        self,
        n_samples: int,
    ) -> List[Dict[str, Any]]:
        """Generate Sobol sequence (Quasi-Monte Carlo).

        Args:
            n_samples: Number of samples.

        Returns:
            List of parameter combinations.
        """
        try:
            from scipy.stats import qmc

            # Get parameter bounds
            names = list(self.parameters.keys())
            n_params = len(names)

            # Create Sobol sampler
            sampler = qmc.Sobol(d=n_params, scramble=True)
            unit_samples = sampler.random(n=n_samples)

            # Map unit samples to parameter values
            self.samples = []
            for unit_sample in unit_samples:
                sample = {}
                for i, name in enumerate(names):
                    values = self.parameters[name]
                    # Map [0, 1] to discrete indices
                    idx = int(unit_sample[i] * len(values))
                    idx = min(idx, len(values) - 1)
                    sample[name] = values[idx]
                self.samples.append(sample)

            return self.samples

        except ImportError:
            print("Warning: scipy not installed, falling back to random sampling")
            return self.generate_random(n_samples)

    def generate_latin_hypercube(
        self,
        n_samples: int,
        seed: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Generate Latin Hypercube samples.

        Args:
            n_samples: Number of samples.
            seed: Random seed.

        Returns:
            List of parameter combinations.
        """
        try:
            from scipy.stats import qmc

            names = list(self.parameters.keys())
            n_params = len(names)

            # Create LHS sampler
            sampler = qmc.LatinHypercube(d=n_params, seed=seed)
            unit_samples = sampler.random(n=n_samples)

            # Map to parameter values
            self.samples = []
            for unit_sample in unit_samples:
                sample = {}
                for i, name in enumerate(names):
                    values = self.parameters[name]
                    idx = int(unit_sample[i] * len(values))
                    idx = min(idx, len(values) - 1)
                    sample[name] = values[idx]
                self.samples.append(sample)

            return self.samples

        except ImportError:
            print("Warning: scipy not installed, falling back to random sampling")
            return self.generate_random(n_samples, seed)

    def save_json(
        self,
        filepath: str | Path,
    ) -> Path:
        """Save parameter sweep to JSON file.

        Args:
            filepath: Output JSON file path.

        Returns:
            Path to saved file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "n_samples": len(self.samples),
            "parameters": list(self.parameters.keys()),
            "samples": self.samples,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath

    def load_json(
        self,
        filepath: str | Path,
    ) -> List[Dict[str, Any]]:
        """Load parameter sweep from JSON file.

        Args:
            filepath: JSON file path.

        Returns:
            List of parameter combinations.
        """
        filepath = Path(filepath)

        with open(filepath, "r") as f:
            data = json.load(f)

        self.samples = data["samples"]
        return self.samples

    def get_sample(
        self,
        index: int,
    ) -> Dict[str, Any]:
        """Get parameter sample by index.

        Args:
            index: Sample index (0-based).

        Returns:
            Parameter dictionary.
        """
        if 0 <= index < len(self.samples):
            return self.samples[index]
        raise IndexError(f"Sample index {index} out of range")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about parameter sweep.

        Returns:
            Statistics dictionary.
        """
        if not self.samples:
            return {}

        stats = {
            "n_samples": len(self.samples),
            "n_parameters": len(self.parameters),
            "parameters": {},
        }

        # Per-parameter statistics
        for name in self.parameters.keys():
            values = [sample[name] for sample in self.samples]

            # Try numeric statistics
            try:
                numeric_values = [float(v) for v in values]
                stats["parameters"][name] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values),
                    "unique_count": len(set(values)),
                }
            except (ValueError, TypeError):
                # Non-numeric parameter
                stats["parameters"][name] = {
                    "unique_count": len(set(map(str, values))),
                    "sample_values": list(set(map(str, values)))[:5],
                }

        return stats
