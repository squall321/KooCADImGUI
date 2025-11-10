"""
Test data factories using Faker.

This module provides factories for generating realistic test data for
parameters, components, and CAD models.
"""

import random
from typing import Any, Dict, List, Optional

from faker import Faker

from koocad.core.parameters import (
    BoolParameter,
    EnumParameter,
    ExpressionParameter,
    FloatParameter,
    IntParameter,
    ParameterSet,
    Unit,
)

fake = Faker()


class ParameterFactory:
    """Base factory for generating parameter objects."""

    @staticmethod
    def create_float(
        name: Optional[str] = None,
        value: Optional[float] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        unit: Optional[Unit] = None,
    ) -> FloatParameter:
        """Create a random FloatParameter.

        Args:
            name: Parameter name (generated if not provided).
            value: Parameter value (generated if not provided).
            min_value: Minimum value constraint.
            max_value: Maximum value constraint.
            unit: Unit of measurement.

        Returns:
            FloatParameter instance.

        Example:
            >>> param = ParameterFactory.create_float(name="width", min_value=0, max_value=20)
            >>> assert 0 <= param.value <= 20
        """
        name = name or fake.word()
        min_val = min_value if min_value is not None else 0.0
        max_val = max_value if max_value is not None else 100.0
        value = value if value is not None else random.uniform(min_val, max_val)

        return FloatParameter(
            name=name,
            description=fake.sentence(),
            value=value,
            min_value=min_value,
            max_value=max_value,
            unit=unit or random.choice(list(Unit)),
        )

    @staticmethod
    def create_int(
        name: Optional[str] = None,
        value: Optional[int] = None,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> IntParameter:
        """Create a random IntParameter.

        Args:
            name: Parameter name (generated if not provided).
            value: Parameter value (generated if not provided).
            min_value: Minimum value constraint.
            max_value: Maximum value constraint.

        Returns:
            IntParameter instance.
        """
        name = name or fake.word()
        min_val = min_value if min_value is not None else 1
        max_val = max_value if max_value is not None else 100
        value = value if value is not None else random.randint(min_val, max_val)

        return IntParameter(
            name=name,
            description=fake.sentence(),
            value=value,
            min_value=min_value,
            max_value=max_value,
        )

    @staticmethod
    def create_bool(
        name: Optional[str] = None,
        value: Optional[bool] = None,
    ) -> BoolParameter:
        """Create a random BoolParameter."""
        name = name or fake.word()
        value = value if value is not None else fake.boolean()

        return BoolParameter(
            name=name,
            description=fake.sentence(),
            value=value,
        )

    @staticmethod
    def create_enum(
        name: Optional[str] = None,
        choices: Optional[List[str]] = None,
        value: Optional[str] = None,
    ) -> EnumParameter:
        """Create a random EnumParameter."""
        name = name or fake.word()
        choices = choices or [fake.word() for _ in range(random.randint(2, 5))]
        value = value if value is not None else random.choice(choices)

        return EnumParameter(
            name=name,
            description=fake.sentence(),
            value=value,
            choices=choices,
        )


class BGAParameterFactory:
    """Factory for generating BGA package parameters."""

    @staticmethod
    def create_basic() -> ParameterSet:
        """Create a basic BGA parameter set.

        Returns:
            ParameterSet with typical BGA parameters.

        Example:
            >>> params = BGAParameterFactory.create_basic()
            >>> assert params.get("substrate_width") is not None
        """
        param_set = ParameterSet()

        # Substrate dimensions
        substrate_width = random.uniform(8.0, 20.0)
        param_set.add(
            FloatParameter(
                name="substrate_width",
                description="BGA substrate width",
                value=substrate_width,
                min_value=5.0,
                max_value=50.0,
                unit=Unit.MM,
            )
        )

        param_set.add(
            FloatParameter(
                name="substrate_height",
                description="BGA substrate height",
                value=substrate_width,  # Square by default
                min_value=5.0,
                max_value=50.0,
                unit=Unit.MM,
            )
        )

        param_set.add(
            FloatParameter(
                name="substrate_thickness",
                description="BGA substrate thickness",
                value=random.uniform(0.6, 1.2),
                min_value=0.3,
                max_value=2.0,
                unit=Unit.MM,
            )
        )

        # Ball array
        ball_rows = random.choice([10, 12, 15, 20, 25])
        param_set.add(
            IntParameter(
                name="ball_rows",
                description="Number of ball rows",
                value=ball_rows,
                min_value=2,
                max_value=50,
            )
        )

        param_set.add(
            IntParameter(
                name="ball_cols",
                description="Number of ball columns",
                value=ball_rows,  # Square array
                min_value=2,
                max_value=50,
            )
        )

        param_set.add(
            FloatParameter(
                name="ball_pitch",
                description="Distance between ball centers",
                value=random.choice([0.4, 0.5, 0.65, 0.8, 1.0]),
                min_value=0.3,
                max_value=1.27,
                unit=Unit.MM,
            )
        )

        param_set.add(
            FloatParameter(
                name="ball_diameter",
                description="Solder ball diameter",
                value=random.uniform(0.3, 0.6),
                min_value=0.2,
                max_value=0.8,
                unit=Unit.MM,
            )
        )

        # Ball pattern
        param_set.add(
            EnumParameter(
                name="ball_pattern",
                description="Ball array pattern",
                value=random.choice(["full", "peripheral"]),
                choices=["full", "peripheral", "custom"],
            )
        )

        # Soldermask
        param_set.add(
            BoolParameter(
                name="enable_soldermask",
                description="Add soldermask layer",
                value=True,
            )
        )

        param_set.add(
            EnumParameter(
                name="soldermask_finish",
                description="Soldermask pad definition",
                value="NSMD",
                choices=["NSMD", "SMD"],
            )
        )

        # Layer count
        param_set.add(
            IntParameter(
                name="layer_count",
                description="Number of substrate layers",
                value=random.choice([2, 4, 6, 8]),
                min_value=2,
                max_value=12,
            )
        )

        return param_set

    @staticmethod
    def create_with_expressions() -> ParameterSet:
        """Create BGA parameters with expression-based derived values."""
        param_set = BGAParameterFactory.create_basic()

        # Add derived parameters
        param_set.add(
            ExpressionParameter(
                name="array_width",
                description="Total width of ball array",
                value="(ball_cols - 1) * ball_pitch",
                dependencies=["ball_cols", "ball_pitch"],
            )
        )

        param_set.add(
            ExpressionParameter(
                name="array_height",
                description="Total height of ball array",
                value="(ball_rows - 1) * ball_pitch",
                dependencies=["ball_rows", "ball_pitch"],
            )
        )

        param_set.add(
            ExpressionParameter(
                name="total_balls",
                description="Total number of balls",
                value="ball_rows * ball_cols",
                dependencies=["ball_rows", "ball_cols"],
            )
        )

        return param_set

    @staticmethod
    def create_batch(count: int = 10) -> List[ParameterSet]:
        """Create multiple BGA parameter sets for batch testing.

        Args:
            count: Number of parameter sets to generate.

        Returns:
            List of ParameterSet instances.
        """
        return [BGAParameterFactory.create_basic() for _ in range(count)]


class MLCCParameterFactory:
    """Factory for generating MLCC (Multi-Layer Ceramic Capacitor) parameters."""

    @staticmethod
    def create_basic() -> ParameterSet:
        """Create a basic MLCC parameter set."""
        param_set = ParameterSet()

        # Body dimensions (EIA standard sizes)
        size_code = random.choice(["0402", "0603", "0805", "1206", "1210"])
        size_map = {
            "0402": (1.0, 0.5, 0.5),
            "0603": (1.6, 0.8, 0.8),
            "0805": (2.0, 1.25, 1.25),
            "1206": (3.2, 1.6, 1.6),
            "1210": (3.2, 2.5, 2.5),
        }
        length, width, height = size_map[size_code]

        param_set.add(
            FloatParameter(
                name="body_length",
                description="MLCC body length",
                value=length,
                min_value=0.5,
                max_value=5.0,
                unit=Unit.MM,
            )
        )

        param_set.add(
            FloatParameter(
                name="body_width",
                description="MLCC body width",
                value=width,
                min_value=0.3,
                max_value=3.0,
                unit=Unit.MM,
            )
        )

        param_set.add(
            FloatParameter(
                name="body_height",
                description="MLCC body height",
                value=height,
                min_value=0.3,
                max_value=3.0,
                unit=Unit.MM,
            )
        )

        # Termination
        param_set.add(
            FloatParameter(
                name="termination_width",
                description="End termination width",
                value=width * 0.8,
                min_value=0.2,
                max_value=2.0,
                unit=Unit.MM,
            )
        )

        param_set.add(
            FloatParameter(
                name="termination_length",
                description="End termination length",
                value=random.uniform(0.25, 0.5),
                min_value=0.15,
                max_value=0.8,
                unit=Unit.MM,
            )
        )

        # Dielectric layers
        param_set.add(
            IntParameter(
                name="layer_count",
                description="Number of dielectric layers",
                value=random.choice([50, 100, 200, 300]),
                min_value=10,
                max_value=1000,
            )
        )

        param_set.add(
            FloatParameter(
                name="layer_thickness",
                description="Individual layer thickness",
                value=random.uniform(1.0, 5.0),
                min_value=0.5,
                max_value=10.0,
                unit=Unit.UM,
            )
        )

        # Electrode pattern
        param_set.add(
            BoolParameter(
                name="show_electrodes",
                description="Show internal electrode pattern",
                value=fake.boolean(),
            )
        )

        return param_set


class ParameterSweepFactory:
    """Factory for generating parameter sweep configurations."""

    @staticmethod
    def create_cartesian_sweep(
        param_ranges: Dict[str, List[Any]],
    ) -> List[Dict[str, Any]]:
        """Create Cartesian product parameter sweep.

        Args:
            param_ranges: Dictionary mapping parameter names to value lists.

        Returns:
            List of parameter dictionaries (Cartesian product).

        Example:
            >>> ranges = {"width": [10, 12, 14], "height": [5, 7]}
            >>> sweep = ParameterSweepFactory.create_cartesian_sweep(ranges)
            >>> assert len(sweep) == 6  # 3 * 2
        """
        import itertools

        keys = list(param_ranges.keys())
        values = list(param_ranges.values())

        sweep_configs = []
        for combination in itertools.product(*values):
            config = dict(zip(keys, combination))
            sweep_configs.append(config)

        return sweep_configs

    @staticmethod
    def create_random_sweep(
        param_ranges: Dict[str, tuple[float, float]],
        count: int = 100,
    ) -> List[Dict[str, float]]:
        """Create random parameter sweep (Monte Carlo).

        Args:
            param_ranges: Dictionary mapping parameter names to (min, max) tuples.
            count: Number of random samples to generate.

        Returns:
            List of parameter dictionaries with random values.

        Example:
            >>> ranges = {"width": (5.0, 20.0), "height": (3.0, 15.0)}
            >>> sweep = ParameterSweepFactory.create_random_sweep(ranges, count=50)
            >>> assert len(sweep) == 50
        """
        sweep_configs = []
        for _ in range(count):
            config = {}
            for param_name, (min_val, max_val) in param_ranges.items():
                config[param_name] = random.uniform(min_val, max_val)
            sweep_configs.append(config)

        return sweep_configs
