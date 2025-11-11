"""
Pytest test suite for KooCAD validation module.

Tests for parameter validation and constraints.
"""

import pytest
from koocad.core.validation import (
    RangeValidator,
    TypeValidator,
    ParameterSetValidator,
    ValidatorChain,
    ValidationSeverity,
)
from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet


class TestRangeValidator:
    """Test RangeValidator functionality."""

    def test_value_within_range(self):
        """Test validation of value within range."""
        validator = RangeValidator(min_value=0.0, max_value=100.0)
        param = FloatParameter(name="test", value=50.0)

        result = validator.validate(50.0, param)

        assert result.severity == ValidationSeverity.INFO

    def test_value_below_minimum(self):
        """Test validation of value below minimum."""
        validator = RangeValidator(min_value=0.0, max_value=100.0)
        param = FloatParameter(name="test", value=-10.0)

        result = validator.validate(-10.0, param)

        assert result.severity == ValidationSeverity.ERROR

    def test_value_above_maximum(self):
        """Test validation of value above maximum."""
        validator = RangeValidator(min_value=0.0, max_value=100.0)
        param = FloatParameter(name="test", value=150.0)

        result = validator.validate(150.0, param)

        assert result.severity == ValidationSeverity.ERROR

    def test_range_validator_with_only_min(self):
        """Test RangeValidator with only minimum value."""
        validator = RangeValidator(min_value=0.0)
        param = FloatParameter(name="test", value=50.0)

        result = validator.validate(50.0, param)
        assert result.severity == ValidationSeverity.INFO

        result2 = validator.validate(-10.0, param)
        assert result2.severity == ValidationSeverity.ERROR

    def test_range_validator_with_only_max(self):
        """Test RangeValidator with only maximum value."""
        validator = RangeValidator(max_value=100.0)
        param = FloatParameter(name="test", value=50.0)

        result = validator.validate(50.0, param)
        assert result.severity == ValidationSeverity.INFO

        result2 = validator.validate(150.0, param)
        assert result2.severity == ValidationSeverity.ERROR


class TestTypeValidator:
    """Test TypeValidator functionality."""

    def test_correct_type(self):
        """Test validation of correct type."""
        validator = TypeValidator(expected_type=float)
        param = FloatParameter(name="test", value=10.0)

        result = validator.validate(10.0, param)

        assert result.severity == ValidationSeverity.INFO

    def test_incorrect_type(self):
        """Test validation of incorrect type."""
        validator = TypeValidator(expected_type=float)
        param = FloatParameter(name="test", value=10.0)

        result = validator.validate("not a float", param)

        assert result.severity == ValidationSeverity.ERROR

    def test_type_validator_with_int(self):
        """Test TypeValidator with integer type."""
        validator = TypeValidator(expected_type=int)
        param = IntParameter(name="test", value=10)

        result = validator.validate(10, param)
        assert result.severity == ValidationSeverity.INFO


class TestValidatorChain:
    """Test ValidatorChain functionality."""

    def test_empty_chain(self):
        """Test empty validator chain."""
        chain = ValidatorChain()
        param = FloatParameter(name="test", value=50.0)

        results = chain.validate(50.0, param)

        assert len(results) == 0

    def test_chain_with_single_validator(self):
        """Test chain with single validator."""
        chain = ValidatorChain()
        chain.add(RangeValidator(min_value=0.0, max_value=100.0))
        param = FloatParameter(name="test", value=50.0)

        results = chain.validate(50.0, param)

        assert len(results) == 1

    def test_chain_with_multiple_validators(self):
        """Test chain with multiple validators."""
        chain = ValidatorChain()
        chain.add(RangeValidator(min_value=0.0, max_value=100.0))
        chain.add(TypeValidator(expected_type=float))
        param = FloatParameter(name="test", value=50.0)

        results = chain.validate(50.0, param)

        assert len(results) == 2

    def test_chain_all_pass(self):
        """Test chain where all validators pass."""
        chain = ValidatorChain()
        chain.add(RangeValidator(min_value=0.0, max_value=100.0))
        chain.add(TypeValidator(expected_type=float))
        param = FloatParameter(name="test", value=50.0)

        results = chain.validate(50.0, param)

        assert all(r.severity == ValidationSeverity.INFO for r in results)

    def test_chain_some_fail(self):
        """Test chain where some validators fail."""
        chain = ValidatorChain()
        chain.add(RangeValidator(min_value=0.0, max_value=100.0))
        chain.add(TypeValidator(expected_type=float))
        param = FloatParameter(name="test", value=150.0)

        results = chain.validate(150.0, param)

        # Range validator should fail, type validator should pass
        assert any(r.severity == ValidationSeverity.ERROR for r in results)


class TestParameterSetValidator:
    """Test ParameterSetValidator functionality."""

    def test_validate_empty_set(self):
        """Test validation of empty parameter set."""
        validator = ParameterSetValidator()
        param_set = ParameterSet()

        results = validator.validate(param_set)

        assert len(results) == 0

    def test_validate_set_with_validators(self):
        """Test validation of parameter set with validators."""
        validator = ParameterSetValidator()
        validator.add_validator("width", RangeValidator(min_value=0.0, max_value=100.0))

        param_set = ParameterSet()
        param_set.add(FloatParameter(name="width", value=50.0))

        results = validator.validate(param_set)

        assert "width" in results
        assert len(results["width"]) > 0

    def test_validate_multiple_parameters(self):
        """Test validation of multiple parameters."""
        validator = ParameterSetValidator()
        validator.add_validator("width", RangeValidator(min_value=0.0, max_value=100.0))
        validator.add_validator("height", RangeValidator(min_value=0.0, max_value=100.0))

        param_set = ParameterSet()
        param_set.add(FloatParameter(name="width", value=50.0))
        param_set.add(FloatParameter(name="height", value=75.0))

        results = validator.validate(param_set)

        assert "width" in results
        assert "height" in results


class TestValidationSeverity:
    """Test ValidationSeverity enum."""

    def test_severity_levels(self):
        """Test ValidationSeverity has correct levels."""
        assert hasattr(ValidationSeverity, "INFO")
        assert hasattr(ValidationSeverity, "WARNING")
        assert hasattr(ValidationSeverity, "ERROR")


# Run tests with pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
