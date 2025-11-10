"""
Tests for parameter validation framework.
"""

import pytest

from koocad.core.parameters import FloatParameter, ParameterSet, Unit
from koocad.core.validation import (
    FunctionValidator,
    ParameterSetValidator,
    RangeValidator,
    TypeValidator,
    ValidationResult,
    ValidationSeverity,
    ValidatorChain,
)


def test_range_validator():
    """Test range validation."""
    validator = RangeValidator(min_value=0.0, max_value=100.0)
    param = FloatParameter(name="test", value=50.0)

    result = validator.validate(50.0, param)
    assert result.is_valid

    result = validator.validate(-10.0, param)
    assert not result.is_valid
    assert result.severity == ValidationSeverity.ERROR


def test_type_validator():
    """Test type validation."""
    validator = TypeValidator(expected_type=float)
    param = FloatParameter(name="test", value=50.0)

    result = validator.validate(50.0, param)
    assert result.is_valid

    result = validator.validate("not a float", param)
    assert not result.is_valid


def test_function_validator():
    """Test custom function validation."""

    def is_even(value: float) -> bool:
        return int(value) % 2 == 0

    validator = FunctionValidator(func=is_even, message="Value must be even")
    param = FloatParameter(name="test", value=50.0)

    result = validator.validate(50.0, param)
    assert result.is_valid

    result = validator.validate(51.0, param)
    assert not result.is_valid


def test_validator_chain():
    """Test validator chaining."""
    chain = ValidatorChain()
    chain.add(RangeValidator(min_value=0.0, max_value=100.0))
    chain.add(TypeValidator(expected_type=float))

    param = FloatParameter(name="test", value=50.0)

    results = chain.validate(50.0, param)
    assert all(r.is_valid for r in results)

    results = chain.validate(-10.0, param)
    assert any(not r.is_valid for r in results)


def test_parameter_set_validator():
    """Test parameter set validation."""
    param_set = ParameterSet()
    param_set.add(
        FloatParameter(
            name="width",
            value=50.0,
            min_value=0.0,
            max_value=100.0,
        )
    )
    param_set.add(
        FloatParameter(
            name="height",
            value=30.0,
            min_value=0.0,
            max_value=100.0,
        )
    )

    validator = ParameterSetValidator()
    validator.add_validator("width", RangeValidator(min_value=0.0, max_value=100.0))
    validator.add_validator("height", RangeValidator(min_value=0.0, max_value=100.0))

    results = validator.validate(param_set)
    assert "width" in results
    assert "height" in results
    assert all(r.is_valid for results_list in results.values() for r in results_list)


def test_validation_with_suggested_value():
    """Test that validation provides suggested values."""
    validator = RangeValidator(min_value=0.0, max_value=100.0)
    param = FloatParameter(name="test", value=-10.0)

    result = validator.validate(-10.0, param)
    assert not result.is_valid
    assert result.suggested_value == 0.0


@pytest.mark.asyncio
async def test_async_validation():
    """Test async validation."""
    chain = ValidatorChain()
    chain.add(RangeValidator(min_value=0.0, max_value=100.0))

    param = FloatParameter(name="test", value=50.0)

    results = await chain.validate_async(50.0, param)
    assert all(r.is_valid for r in results)
