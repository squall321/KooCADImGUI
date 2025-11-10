"""
Pytest test suite for KooCAD parameter system.

This module contains unit tests for the core parameter functionality.
"""

import pytest
from koocad.core.parameters import (
    FloatParameter,
    IntParameter,
    BoolParameter,
    StringParameter,
    ExpressionParameter,
    ParameterSet,
    Unit,
)
from koocad.core.expressions import ExpressionEngine


class TestParameterCreation:
    """Test parameter creation and initialization."""

    def test_float_parameter_creation(self):
        """Test FloatParameter creation with keyword arguments."""
        fp = FloatParameter(
            name='width',
            value=10.0,
            min_value=0.0,
            max_value=100.0,
            unit=Unit.MM,
        )

        assert fp.name == 'width'
        assert fp.value == 10.0
        assert fp.min_value == 0.0
        assert fp.max_value == 100.0
        assert fp.unit == Unit.MM

    def test_int_parameter_creation(self):
        """Test IntParameter creation."""
        ip = IntParameter(
            name='count',
            value=15,
            min_value=1,
            max_value=50,
        )

        assert ip.name == 'count'
        assert ip.value == 15
        assert ip.min_value == 1
        assert ip.max_value == 50

    def test_bool_parameter_creation(self):
        """Test BoolParameter creation."""
        bp = BoolParameter(name='enable_feature', value=True)

        assert bp.name == 'enable_feature'
        assert bp.value is True

    def test_string_parameter_creation(self):
        """Test StringParameter creation."""
        sp = StringParameter(name='material', value='copper')

        assert sp.name == 'material'
        assert sp.value == 'copper'


class TestParameterValidation:
    """Test parameter validation."""

    def test_valid_value(self):
        """Test validation with valid value."""
        fp = FloatParameter(name='test', value=50.0, min_value=0.0, max_value=100.0)

        # Should not raise exception
        assert fp.validate_value(50.0) is True

    def test_invalid_value_too_high(self):
        """Test validation with value too high."""
        fp = FloatParameter(name='test', value=50.0, min_value=0.0, max_value=100.0)

        with pytest.raises(ValueError):
            fp.validate_value(150.0)

    def test_invalid_value_too_low(self):
        """Test validation with value too low."""
        fp = FloatParameter(name='test', value=50.0, min_value=0.0, max_value=100.0)

        with pytest.raises(ValueError):
            fp.validate_value(-10.0)


class TestExpressionEngine:
    """Test expression engine functionality."""

    def test_simple_expression(self):
        """Test simple mathematical expression."""
        engine = ExpressionEngine()
        context = {'a': 10.0, 'b': 20.0}

        result = engine.evaluate('a + b', context)
        assert result == 30.0

    def test_complex_expression(self):
        """Test complex expression with multiple operations."""
        engine = ExpressionEngine()
        context = {'width': 10.0, 'height': 20.0}

        result = engine.evaluate('width * height / 2', context)
        assert result == 100.0

    def test_mathematical_functions(self):
        """Test mathematical functions."""
        engine = ExpressionEngine()
        context = {'x': 4.0, 'y': 9.0}

        result_sqrt = engine.evaluate('sqrt(x)', context)
        assert result_sqrt == 2.0

        result_max = engine.evaluate('max(x, y)', context)
        assert result_max == 9.0

    def test_constants(self):
        """Test built-in constants."""
        engine = ExpressionEngine()

        result_pi = engine.evaluate('pi * 2', {})
        assert abs(result_pi - 6.283185) < 0.0001

    def test_extract_variables(self):
        """Test variable extraction from expression."""
        engine = ExpressionEngine()

        variables = engine.extract_variables('a + b * c - d')
        assert variables == {'a', 'b', 'c', 'd'}


class TestParameterSet:
    """Test ParameterSet functionality."""

    def test_add_parameter(self):
        """Test adding parameters to set."""
        param_set = ParameterSet()
        fp = FloatParameter(name='width', value=10.0)

        param_set.add(fp)

        assert 'width' in param_set.parameters
        assert len(param_set.parameters) == 1

    def test_get_parameter(self):
        """Test retrieving parameter from set."""
        param_set = ParameterSet()
        fp = FloatParameter(name='width', value=10.0)
        param_set.add(fp)

        retrieved = param_set.get('width')

        assert retrieved is not None
        assert retrieved.name == 'width'
        assert retrieved.value == 10.0

    def test_set_value(self):
        """Test setting parameter value."""
        param_set = ParameterSet()
        fp = FloatParameter(name='width', value=10.0, min_value=0.0, max_value=100.0)
        param_set.add(fp)

        param_set.set_value('width', 15.0)

        assert param_set.get('width').value == 15.0

    def test_evaluate_all(self):
        """Test evaluating all parameters."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name='width', value=10.0))
        param_set.add(FloatParameter(name='height', value=20.0))

        values = param_set.evaluate_all()

        assert values['width'] == 10.0
        assert values['height'] == 20.0


class TestExpressionParameter:
    """Test ExpressionParameter functionality."""

    def test_expression_parameter_creation(self):
        """Test ExpressionParameter creation."""
        ep = ExpressionParameter(
            name='area',
            value='width * height',
        )

        assert ep.name == 'area'
        assert ep.value == 'width * height'

    def test_expression_evaluation_with_dependencies(self):
        """Test expression evaluation with dependencies."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name='width', value=10.0))
        param_set.add(FloatParameter(name='height', value=20.0))
        param_set.add(ExpressionParameter(name='area', value='width * height'))

        values = param_set.evaluate_all()

        assert values['width'] == 10.0
        assert values['height'] == 20.0
        assert values['area'] == 200.0

    def test_complex_dependency_chain(self):
        """Test complex dependency chain."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name='a', value=2.0))
        param_set.add(FloatParameter(name='b', value=3.0))
        param_set.add(ExpressionParameter(name='c', value='a + b'))
        param_set.add(ExpressionParameter(name='d', value='c * 2'))

        values = param_set.evaluate_all()

        assert values['a'] == 2.0
        assert values['b'] == 3.0
        assert values['c'] == 5.0
        assert values['d'] == 10.0


class TestUnitConversion:
    """Test unit conversion functionality."""

    def test_mm_to_base(self):
        """Test millimeter conversion (base unit)."""
        fp = FloatParameter(name='width', value=10.0, unit=Unit.MM)
        assert fp.to_base_unit() == 10.0

    def test_inch_to_mm(self):
        """Test inch to millimeter conversion."""
        fp = FloatParameter(name='width', value=1.0, unit=Unit.INCH)
        assert abs(fp.to_base_unit() - 25.4) < 0.001

    def test_mil_to_mm(self):
        """Test mil to millimeter conversion."""
        fp = FloatParameter(name='width', value=1.0, unit=Unit.MIL)
        assert abs(fp.to_base_unit() - 0.0254) < 0.00001


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
