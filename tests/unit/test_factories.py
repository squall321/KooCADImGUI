"""Tests for test data factories."""

import pytest

from koocad.core.parameters import Unit
from koocad.testing.factories import (
    BGAParameterFactory,
    MLCCParameterFactory,
    ParameterFactory,
    ParameterSweepFactory,
)


class TestParameterFactory:
    """Tests for ParameterFactory."""

    def test_create_float(self) -> None:
        """Test creating float parameter."""
        param = ParameterFactory.create_float(
            name="width",
            min_value=0.0,
            max_value=10.0,
        )

        assert param.name == "width"
        assert 0.0 <= param.value <= 10.0
        assert param.min_value == 0.0
        assert param.max_value == 10.0

    def test_create_int(self) -> None:
        """Test creating integer parameter."""
        param = ParameterFactory.create_int(
            name="count",
            min_value=1,
            max_value=100,
        )

        assert param.name == "count"
        assert 1 <= param.value <= 100

    def test_create_bool(self) -> None:
        """Test creating boolean parameter."""
        param = ParameterFactory.create_bool(name="enabled")

        assert param.name == "enabled"
        assert isinstance(param.value, bool)

    def test_create_enum(self) -> None:
        """Test creating enum parameter."""
        choices = ["option1", "option2", "option3"]
        param = ParameterFactory.create_enum(
            name="mode",
            choices=choices,
        )

        assert param.name == "mode"
        assert param.value in choices
        assert param.choices == choices


class TestBGAParameterFactory:
    """Tests for BGAParameterFactory."""

    def test_create_basic(self) -> None:
        """Test creating basic BGA parameters."""
        params = BGAParameterFactory.create_basic()

        # Check essential parameters exist
        assert params.get("substrate_width") is not None
        assert params.get("substrate_height") is not None
        assert params.get("substrate_thickness") is not None
        assert params.get("ball_rows") is not None
        assert params.get("ball_cols") is not None
        assert params.get("ball_pitch") is not None
        assert params.get("ball_diameter") is not None

        # Verify parameter types
        substrate_width = params.get("substrate_width")
        assert substrate_width.unit == Unit.MM

        ball_rows = params.get("ball_rows")
        assert ball_rows.value >= 2

    def test_create_with_expressions(self) -> None:
        """Test creating BGA parameters with expressions."""
        params = BGAParameterFactory.create_with_expressions()

        # Check derived parameters exist
        assert params.get("array_width") is not None
        assert params.get("array_height") is not None
        assert params.get("total_balls") is not None

        # Evaluate all parameters
        result = params.evaluate_all()

        # Verify expressions are evaluated correctly
        ball_rows = params.get("ball_rows").value
        ball_cols = params.get("ball_cols").value
        assert result["total_balls"] == pytest.approx(ball_rows * ball_cols)

    def test_create_batch(self) -> None:
        """Test creating batch of BGA parameters."""
        batch_size = 5
        batch = BGAParameterFactory.create_batch(count=batch_size)

        assert len(batch) == batch_size
        for params in batch:
            assert params.get("substrate_width") is not None


class TestMLCCParameterFactory:
    """Tests for MLCCParameterFactory."""

    def test_create_basic(self) -> None:
        """Test creating basic MLCC parameters."""
        params = MLCCParameterFactory.create_basic()

        # Check essential parameters
        assert params.get("body_length") is not None
        assert params.get("body_width") is not None
        assert params.get("body_height") is not None
        assert params.get("layer_count") is not None

        # Verify reasonable values
        layer_count = params.get("layer_count")
        assert layer_count.value >= 10


class TestParameterSweepFactory:
    """Tests for ParameterSweepFactory."""

    def test_cartesian_sweep(self) -> None:
        """Test Cartesian product sweep generation."""
        param_ranges = {
            "width": [10, 12, 14],
            "height": [5, 7],
        }

        sweep = ParameterSweepFactory.create_cartesian_sweep(param_ranges)

        # Should generate 3 * 2 = 6 combinations
        assert len(sweep) == 6

        # Check all combinations present
        widths = {config["width"] for config in sweep}
        heights = {config["height"] for config in sweep}

        assert widths == {10, 12, 14}
        assert heights == {5, 7}

    def test_random_sweep(self) -> None:
        """Test random sweep generation."""
        param_ranges = {
            "width": (5.0, 20.0),
            "height": (3.0, 15.0),
        }

        count = 50
        sweep = ParameterSweepFactory.create_random_sweep(param_ranges, count=count)

        assert len(sweep) == count

        # Verify all values within range
        for config in sweep:
            assert 5.0 <= config["width"] <= 20.0
            assert 3.0 <= config["height"] <= 15.0
