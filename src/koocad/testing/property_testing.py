"""
Property-based testing utilities for parametric systems.

This module provides Hypothesis-based property testing, fuzzing, and
metamorphic testing capabilities.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Dict, List, Optional, Type

from hypothesis import given, settings, strategies as st
from hypothesis.strategies import SearchStrategy

from koocad.core.parameters import FloatParameter, IntParameter, Parameter, ParameterSet, Unit


class ParameterStrategy:
    """Hypothesis strategies for parameter generation."""

    @staticmethod
    def float_parameter(
        min_value: float = 0.0,
        max_value: float = 100.0,
        unit: Unit = Unit.MM,
    ) -> SearchStrategy[FloatParameter]:
        """Generate valid FloatParameter instances.

        Args:
            min_value: Minimum parameter value.
            max_value: Maximum parameter value.
            unit: Unit for parameter.

        Returns:
            Hypothesis strategy for FloatParameter.
        """
        return st.builds(
            FloatParameter,
            name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
            value=st.floats(min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False),
            min_value=st.just(min_value),
            max_value=st.just(max_value),
            unit=st.just(unit),
        )

    @staticmethod
    def int_parameter(
        min_value: int = 0,
        max_value: int = 100,
    ) -> SearchStrategy[IntParameter]:
        """Generate valid IntParameter instances.

        Args:
            min_value: Minimum parameter value.
            max_value: Maximum parameter value.

        Returns:
            Hypothesis strategy for IntParameter.
        """
        return st.builds(
            IntParameter,
            name=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))),
            value=st.integers(min_value=min_value, max_value=max_value),
            min_value=st.just(min_value),
            max_value=st.just(max_value),
        )

    @staticmethod
    def parameter_set(
        param_count: int = 5,
        float_ratio: float = 0.7,
    ) -> SearchStrategy[ParameterSet]:
        """Generate ParameterSet with mixed parameter types.

        Args:
            param_count: Number of parameters to generate.
            float_ratio: Ratio of float to int parameters (0.0-1.0).

        Returns:
            Hypothesis strategy for ParameterSet.
        """

        def build_param_set(*params: Parameter) -> ParameterSet:
            """Build parameter set from list of parameters."""
            param_set = ParameterSet()
            for param in params:
                param_set.add(param)
            return param_set

        float_count = int(param_count * float_ratio)
        int_count = param_count - float_count

        float_params = st.lists(
            ParameterStrategy.float_parameter(),
            min_size=float_count,
            max_size=float_count,
        )
        int_params = st.lists(
            ParameterStrategy.int_parameter(),
            min_size=int_count,
            max_size=int_count,
        )

        return st.builds(
            build_param_set,
            st.tuples(float_params, int_params).map(lambda x: x[0] + x[1]),
        )


class PropertyTest:
    """Property-based testing helper."""

    @staticmethod
    def test_parameter_immutability(param: Parameter) -> bool:
        """Test that parameter name is immutable.

        Args:
            param: Parameter to test.

        Returns:
            True if name is immutable.
        """
        original_name = param.name
        try:
            param.name = "new_name"  # type: ignore
            return False  # Should not reach here
        except AttributeError:
            return param.name == original_name

    @staticmethod
    def test_parameter_validation(param: FloatParameter) -> bool:
        """Test that parameter respects min/max constraints.

        Args:
            param: FloatParameter to test.

        Returns:
            True if validation works correctly.
        """
        if param.min_value is not None and param.value < param.min_value:
            return False

        if param.max_value is not None and param.value > param.max_value:
            return False

        return True

    @staticmethod
    def test_unit_conversion_roundtrip(param: FloatParameter) -> bool:
        """Test that unit conversion is reversible.

        Args:
            param: FloatParameter to test.

        Returns:
            True if conversion roundtrip preserves value.
        """
        original_value = param.value

        # Convert to base unit and back
        base_value = param.to_base_unit()
        reconstructed = param.from_base_unit(base_value)

        # Allow small floating-point error
        return abs(reconstructed - original_value) < 1e-9

    @staticmethod
    def test_parameter_set_evaluation(param_set: ParameterSet) -> bool:
        """Test that parameter set evaluation is consistent.

        Args:
            param_set: ParameterSet to test.

        Returns:
            True if evaluation is consistent.
        """
        try:
            values1 = param_set.evaluate_all()
            values2 = param_set.evaluate_all()

            # Should get same results on repeated evaluation
            return values1 == values2
        except Exception:
            return False


class Fuzzer:
    """Fuzzing utilities for parameter testing."""

    @staticmethod
    def fuzz_parameter_value(
        param: FloatParameter,
        mutation_rate: float = 0.1,
    ) -> float:
        """Generate fuzzed parameter value.

        Args:
            param: Parameter to fuzz.
            mutation_rate: How much to mutate (0.0-1.0).

        Returns:
            Fuzzed value.
        """
        current = param.value

        # Random mutation strategies
        strategies = [
            lambda: current * (1.0 + random.uniform(-mutation_rate, mutation_rate)),  # Scale
            lambda: current + random.uniform(-mutation_rate * current, mutation_rate * current),  # Add
            lambda: 0.0,  # Zero
            lambda: param.min_value if param.min_value is not None else 0.0,  # Min
            lambda: param.max_value if param.max_value is not None else 100.0,  # Max
            lambda: float("inf"),  # Infinity
            lambda: float("-inf"),  # Negative infinity
            lambda: float("nan"),  # NaN
        ]

        strategy = random.choice(strategies)
        return strategy()

    @staticmethod
    def fuzz_parameter_set(
        param_set: ParameterSet,
        fuzz_count: int = 10,
    ) -> List[ParameterSet]:
        """Generate fuzzed parameter sets.

        Args:
            param_set: Base parameter set.
            fuzz_count: Number of fuzzed sets to generate.

        Returns:
            List of fuzzed parameter sets.
        """
        fuzzed_sets: List[ParameterSet] = []

        for _ in range(fuzz_count):
            new_set = ParameterSet()

            for name, param in param_set.parameters.items():
                if isinstance(param, FloatParameter):
                    fuzzed_value = Fuzzer.fuzz_parameter_value(param)
                    new_param = FloatParameter(
                        name=name,
                        value=fuzzed_value,
                        min_value=param.min_value,
                        max_value=param.max_value,
                        unit=param.unit,
                    )
                    new_set.add(new_param)
                elif isinstance(param, IntParameter):
                    # Fuzz integer values
                    current = param.value
                    fuzzed = random.choice(
                        [
                            current,
                            current + 1,
                            current - 1,
                            param.min_value if param.min_value is not None else 0,
                            param.max_value if param.max_value is not None else 100,
                            0,
                            -1,
                            999999,
                        ]
                    )
                    new_param = IntParameter(
                        name=name,
                        value=fuzzed,
                        min_value=param.min_value,
                        max_value=param.max_value,
                    )
                    new_set.add(new_param)

            fuzzed_sets.append(new_set)

        return fuzzed_sets


class MetamorphicTester:
    """Metamorphic testing for parametric CAD operations."""

    @staticmethod
    def test_scale_invariance(
        generator_func: Callable[[ParameterSet], Any],
        param_set: ParameterSet,
        scale_params: List[str],
        scale_factor: float = 2.0,
    ) -> bool:
        """Test that scaling all dimensions preserves relative geometry.

        Args:
            generator_func: Function that generates CAD model.
            param_set: Base parameter set.
            scale_params: Names of parameters to scale.
            scale_factor: Factor to scale by.

        Returns:
            True if metamorphic property holds.
        """
        # Generate base model
        base_model = generator_func(param_set)

        # Scale parameters
        scaled_set = ParameterSet()
        for name, param in param_set.parameters.items():
            if name in scale_params and isinstance(param, FloatParameter):
                new_param = FloatParameter(
                    name=name,
                    value=param.value * scale_factor,
                    min_value=param.min_value,
                    max_value=param.max_value,
                    unit=param.unit,
                )
                scaled_set.add(new_param)
            else:
                scaled_set.add(param)

        # Generate scaled model
        scaled_model = generator_func(scaled_set)

        # TODO: Compare models (Phase 31-50)
        # For now, just check both succeeded
        return base_model is not None and scaled_model is not None

    @staticmethod
    def test_translation_invariance(
        generator_func: Callable[[ParameterSet], Any],
        param_set: ParameterSet,
    ) -> bool:
        """Test that geometry is invariant to translation.

        Args:
            generator_func: Function that generates CAD model.
            param_set: Base parameter set.

        Returns:
            True if metamorphic property holds.
        """
        # Generate model twice with same parameters
        model1 = generator_func(param_set)
        model2 = generator_func(param_set)

        # Models should be equivalent (TODO: actual comparison in Phase 31-50)
        return model1 is not None and model2 is not None

    @staticmethod
    def test_parameter_monotonicity(
        metric_func: Callable[[Any], float],
        generator_func: Callable[[ParameterSet], Any],
        param_set: ParameterSet,
        param_name: str,
        increasing: bool = True,
    ) -> bool:
        """Test that increasing a parameter monotonically affects a metric.

        Args:
            metric_func: Function that computes metric from model.
            generator_func: Function that generates CAD model.
            param_set: Base parameter set.
            param_name: Parameter to vary.
            increasing: True if metric should increase with parameter.

        Returns:
            True if monotonicity holds.
        """
        param = param_set.get(param_name)
        if param is None or not isinstance(param, FloatParameter):
            return False

        # Generate models with increasing parameter values
        values = [param.value * 0.5, param.value, param.value * 1.5, param.value * 2.0]
        metrics = []

        for value in values:
            test_set = ParameterSet()
            for name, p in param_set.parameters.items():
                if name == param_name:
                    new_param = FloatParameter(
                        name=name,
                        value=value,
                        min_value=p.min_value,
                        max_value=p.max_value,
                        unit=p.unit,
                    )
                    test_set.add(new_param)
                else:
                    test_set.add(p)

            model = generator_func(test_set)
            metric = metric_func(model)
            metrics.append(metric)

        # Check monotonicity
        if increasing:
            return all(metrics[i] <= metrics[i + 1] for i in range(len(metrics) - 1))
        else:
            return all(metrics[i] >= metrics[i + 1] for i in range(len(metrics) - 1))


# Example property tests using Hypothesis
class ExamplePropertyTests:
    """Example property-based tests."""

    @given(ParameterStrategy.float_parameter())
    @settings(max_examples=100)
    def test_float_parameter_validity(self, param: FloatParameter) -> None:
        """Test that generated float parameters are valid."""
        assert PropertyTest.test_parameter_validation(param)
        assert PropertyTest.test_unit_conversion_roundtrip(param)

    @given(ParameterStrategy.int_parameter())
    @settings(max_examples=100)
    def test_int_parameter_validity(self, param: IntParameter) -> None:
        """Test that generated int parameters are valid."""
        assert param.value >= (param.min_value if param.min_value is not None else float("-inf"))
        assert param.value <= (param.max_value if param.max_value is not None else float("inf"))

    @given(ParameterStrategy.parameter_set(param_count=10))
    @settings(max_examples=50)
    def test_parameter_set_consistency(self, param_set: ParameterSet) -> None:
        """Test that parameter sets behave consistently."""
        assert PropertyTest.test_parameter_set_evaluation(param_set)
