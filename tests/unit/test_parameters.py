"""Unit tests for parameter system."""

import pytest

from koocad.core.parameters import (
    BoolParameter,
    EnumParameter,
    ExpressionParameter,
    FloatParameter,
    IntParameter,
    ParameterSet,
    Unit,
)


class TestFloatParameter:
    """Tests for FloatParameter."""

    def test_basic_creation(self) -> None:
        """Test creating a basic float parameter."""
        param = FloatParameter(name="width", value=10.0)
        assert param.name == "width"
        assert param.value == 10.0

    def test_with_constraints(self) -> None:
        """Test float parameter with min/max constraints."""
        param = FloatParameter(
            name="thickness",
            value=0.8,
            min_value=0.1,
            max_value=2.0,
        )

        assert param.value == 0.8

        # Validation should be called externally
        with pytest.raises(ValueError):
            param.validate_value(-0.5)

        with pytest.raises(ValueError):
            param.validate_value(3.0)

    def test_unit_conversion(self) -> None:
        """Test unit conversion to base unit (mm)."""
        # MM to MM
        param_mm = FloatParameter(name="length", value=10.0, unit=Unit.MM)
        assert param_mm.to_base_unit() == 10.0

        # Inch to MM
        param_inch = FloatParameter(name="length", value=1.0, unit=Unit.INCH)
        assert param_inch.to_base_unit() == pytest.approx(25.4)

        # Mil to MM
        param_mil = FloatParameter(name="length", value=1000.0, unit=Unit.MIL)
        assert param_mil.to_base_unit() == pytest.approx(25.4)


class TestIntParameter:
    """Tests for IntParameter."""

    def test_basic_creation(self) -> None:
        """Test creating an integer parameter."""
        param = IntParameter(name="count", value=15)
        assert param.value == 15
        assert param.to_base_unit() == 15.0


class TestBoolParameter:
    """Tests for BoolParameter."""

    def test_basic_creation(self) -> None:
        """Test creating a boolean parameter."""
        param = BoolParameter(name="enabled", value=True)
        assert param.value is True
        assert param.to_base_unit() == 1.0

        param.value = False
        assert param.to_base_unit() == 0.0


class TestEnumParameter:
    """Tests for EnumParameter."""

    def test_valid_choice(self) -> None:
        """Test enum with valid choices."""
        param = EnumParameter(
            name="pattern",
            value="full",
            choices=["full", "peripheral", "custom"],
        )
        assert param.value == "full"
        assert param.to_base_unit() == 0.0  # Index of "full"

    def test_invalid_choice(self) -> None:
        """Test enum with invalid choice raises error."""
        with pytest.raises(ValueError, match="not in choices"):
            EnumParameter(
                name="pattern",
                value="invalid",
                choices=["full", "peripheral"],
            )


class TestExpressionParameter:
    """Tests for ExpressionParameter."""

    def test_simple_expression(self) -> None:
        """Test evaluating a simple expression."""
        param = ExpressionParameter(
            name="inner_width",
            value="outer_width - 2 * wall_thickness",
            dependencies=["outer_width", "wall_thickness"],
        )

        context = {"outer_width": 10.0, "wall_thickness": 0.5}
        result = param.evaluate(context)

        assert result == pytest.approx(9.0)

    def test_missing_dependency(self) -> None:
        """Test that missing dependencies raise error."""
        param = ExpressionParameter(
            name="area",
            value="width * height",
            dependencies=["width", "height"],
        )

        with pytest.raises(ValueError, match="Missing dependency"):
            param.evaluate({"width": 10.0})  # Missing "height"


class TestParameterSet:
    """Tests for ParameterSet."""

    def test_add_and_get(self) -> None:
        """Test adding and retrieving parameters."""
        param_set = ParameterSet()

        param = FloatParameter(name="width", value=10.0)
        param_set.add(param)

        retrieved = param_set.get("width")
        assert retrieved is not None
        assert retrieved.name == "width"
        assert retrieved.value == 10.0

    def test_set_value(self) -> None:
        """Test setting parameter value."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name="height", value=5.0))

        param_set.set_value("height", 7.5)
        assert param_set.get("height").value == 7.5

    def test_evaluate_all_simple(self) -> None:
        """Test evaluating all parameters (no expressions)."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name="width", value=10.0))
        param_set.add(FloatParameter(name="height", value=5.0))

        result = param_set.evaluate_all()

        assert result["width"] == 10.0
        assert result["height"] == 5.0

    def test_evaluate_all_with_expressions(self) -> None:
        """Test evaluating parameters with expressions."""
        param_set = ParameterSet()

        param_set.add(FloatParameter(name="outer_width", value=10.0))
        param_set.add(FloatParameter(name="wall_thickness", value=0.5))
        param_set.add(
            ExpressionParameter(
                name="inner_width",
                value="outer_width - 2 * wall_thickness",
                dependencies=["outer_width", "wall_thickness"],
            )
        )

        result = param_set.evaluate_all()

        assert result["outer_width"] == 10.0
        assert result["wall_thickness"] == 0.5
        assert result["inner_width"] == pytest.approx(9.0)

    def test_circular_dependency_detection(self) -> None:
        """Test that circular dependencies are detected."""
        param_set = ParameterSet()

        param_set.add(
            ExpressionParameter(
                name="a",
                value="b + 1",
                dependencies=["b"],
            )
        )
        param_set.add(
            ExpressionParameter(
                name="b",
                value="a + 1",
                dependencies=["a"],
            )
        )

        with pytest.raises(ValueError, match="Circular dependency"):
            param_set.evaluate_all()

    def test_serialization(self) -> None:
        """Test serialization to/from dict."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name="width", value=10.0))
        param_set.add(IntParameter(name="count", value=15))

        # Serialize
        data = param_set.to_dict()
        assert "parameters" in data
        assert "width" in data["parameters"]

        # Note: Deserialization requires type information
        # This is a simplified test

    def test_checksum(self) -> None:
        """Test checksum computation."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name="width", value=10.0))

        checksum1 = param_set.compute_checksum()
        assert isinstance(checksum1, str)
        assert len(checksum1) == 64  # SHA256 hex length

        # Same parameters should give same checksum
        checksum2 = param_set.compute_checksum()
        assert checksum1 == checksum2

        # Different parameters should give different checksum
        param_set.set_value("width", 20.0)
        checksum3 = param_set.compute_checksum()
        assert checksum1 != checksum3
