"""
Parameter validation framework with validator chaining and async support.

This module provides a comprehensive validation system for parameters.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Optional, Protocol

from koocad.core.parameters import Parameter, ParameterSet


class ValidationSeverity(Enum):
    """Validation severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationResult:
    """Result of validation operation."""

    is_valid: bool
    severity: ValidationSeverity
    message: str
    parameter_name: Optional[str] = None
    suggested_value: Optional[Any] = None

    def __bool__(self) -> bool:
        """Allow truthiness check."""
        return self.is_valid


class Validator(ABC):
    """Base class for parameter validators."""

    def __init__(self, message: str = "", severity: ValidationSeverity = ValidationSeverity.ERROR) -> None:
        """Initialize validator.

        Args:
            message: Custom validation error message.
            severity: Severity level for validation failures.
        """
        self.message = message
        self.severity = severity

    @abstractmethod
    def validate(self, value: Any, param: Parameter) -> ValidationResult:
        """Validate parameter value.

        Args:
            value: Value to validate.
            param: Parameter being validated.

        Returns:
            ValidationResult indicating success/failure.
        """
        ...

    def __call__(self, value: Any, param: Parameter) -> ValidationResult:
        """Allow validator to be called directly."""
        return self.validate(value, param)


class RangeValidator(Validator):
    """Validates value is within a range."""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize range validator.

        Args:
            min_value: Minimum allowed value (inclusive).
            max_value: Maximum allowed value (inclusive).
            **kwargs: Additional validator arguments.
        """
        super().__init__(**kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: Any, param: Parameter) -> ValidationResult:
        """Validate value is within range."""
        if self.min_value is not None and value < self.min_value:
            return ValidationResult(
                is_valid=False,
                severity=self.severity,
                message=self.message or f"Value {value} is below minimum {self.min_value}",
                parameter_name=param.name,
                suggested_value=self.min_value,
            )

        if self.max_value is not None and value > self.max_value:
            return ValidationResult(
                is_valid=False,
                severity=self.severity,
                message=self.message or f"Value {value} exceeds maximum {self.max_value}",
                parameter_name=param.name,
                suggested_value=self.max_value,
            )

        return ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.INFO,
            message="Value within valid range",
            parameter_name=param.name,
        )


class TypeValidator(Validator):
    """Validates value is of correct type."""

    def __init__(self, expected_type: type, **kwargs: Any) -> None:
        """Initialize type validator.

        Args:
            expected_type: Expected Python type.
            **kwargs: Additional validator arguments.
        """
        super().__init__(**kwargs)
        self.expected_type = expected_type

    def validate(self, value: Any, param: Parameter) -> ValidationResult:
        """Validate value type."""
        if not isinstance(value, self.expected_type):
            return ValidationResult(
                is_valid=False,
                severity=self.severity,
                message=self.message
                or f"Expected type {self.expected_type.__name__}, got {type(value).__name__}",
                parameter_name=param.name,
            )

        return ValidationResult(
            is_valid=True,
            severity=ValidationSeverity.INFO,
            message="Type is correct",
            parameter_name=param.name,
        )


class FunctionValidator(Validator):
    """Validates value using custom function."""

    def __init__(self, func: Callable[[Any], bool], **kwargs: Any) -> None:
        """Initialize function validator.

        Args:
            func: Function that returns True if value is valid.
            **kwargs: Additional validator arguments.
        """
        super().__init__(**kwargs)
        self.func = func

    def validate(self, value: Any, param: Parameter) -> ValidationResult:
        """Validate using custom function."""
        try:
            is_valid = self.func(value)
            return ValidationResult(
                is_valid=is_valid,
                severity=self.severity if not is_valid else ValidationSeverity.INFO,
                message=self.message or ("Validation passed" if is_valid else "Validation failed"),
                parameter_name=param.name,
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Validation function raised exception: {e}",
                parameter_name=param.name,
            )


class AsyncValidator(ABC):
    """Base class for async validators (e.g., external API calls)."""

    def __init__(self, message: str = "", severity: ValidationSeverity = ValidationSeverity.ERROR) -> None:
        """Initialize async validator."""
        self.message = message
        self.severity = severity

    @abstractmethod
    async def validate_async(self, value: Any, param: Parameter) -> ValidationResult:
        """Validate parameter value asynchronously.

        Args:
            value: Value to validate.
            param: Parameter being validated.

        Returns:
            ValidationResult indicating success/failure.
        """
        ...


class ValidatorChain:
    """Chain of validators to run sequentially."""

    def __init__(self, validators: Optional[List[Validator]] = None) -> None:
        """Initialize validator chain.

        Args:
            validators: List of validators to add to chain.
        """
        self.validators: List[Validator] = validators or []
        self.async_validators: List[AsyncValidator] = []

    def add(self, validator: Validator) -> ValidatorChain:
        """Add validator to chain.

        Args:
            validator: Validator to add.

        Returns:
            Self for method chaining.
        """
        self.validators.append(validator)
        return self

    def add_async(self, validator: AsyncValidator) -> ValidatorChain:
        """Add async validator to chain.

        Args:
            validator: Async validator to add.

        Returns:
            Self for method chaining.
        """
        self.async_validators.append(validator)
        return self

    def validate(self, value: Any, param: Parameter) -> List[ValidationResult]:
        """Run all synchronous validators.

        Args:
            value: Value to validate.
            param: Parameter being validated.

        Returns:
            List of validation results.
        """
        results: List[ValidationResult] = []

        for validator in self.validators:
            result = validator.validate(value, param)
            results.append(result)

            # Stop on first error if strict mode
            if not result.is_valid and result.severity == ValidationSeverity.ERROR:
                break

        return results

    async def validate_async(self, value: Any, param: Parameter) -> List[ValidationResult]:
        """Run all validators including async ones.

        Args:
            value: Value to validate.
            param: Parameter being validated.

        Returns:
            List of validation results.
        """
        # Run synchronous validators first
        results = self.validate(value, param)

        # Check if any sync validators failed with ERROR
        has_errors = any(r.severity == ValidationSeverity.ERROR and not r.is_valid for r in results)
        if has_errors:
            return results

        # Run async validators
        async_tasks = [validator.validate_async(value, param) for validator in self.async_validators]
        async_results = await asyncio.gather(*async_tasks, return_exceptions=True)

        for result in async_results:
            if isinstance(result, Exception):
                results.append(
                    ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.ERROR,
                        message=f"Async validation failed: {result}",
                        parameter_name=param.name,
                    )
                )
            else:
                results.append(result)

        return results


class ParameterSetValidator:
    """Validates entire parameter sets."""

    def __init__(self) -> None:
        """Initialize parameter set validator."""
        self.validators: dict[str, ValidatorChain] = {}

    def add_validator(self, param_name: str, validator: Validator) -> None:
        """Add validator for specific parameter.

        Args:
            param_name: Parameter name.
            validator: Validator to add.
        """
        if param_name not in self.validators:
            self.validators[param_name] = ValidatorChain()

        self.validators[param_name].add(validator)

    def validate(self, param_set: ParameterSet) -> dict[str, List[ValidationResult]]:
        """Validate entire parameter set.

        Args:
            param_set: ParameterSet to validate.

        Returns:
            Dictionary mapping parameter names to validation results.
        """
        all_results: dict[str, List[ValidationResult]] = {}

        for param_name, param in param_set.parameters.items():
            if param_name in self.validators:
                results = self.validators[param_name].validate(param.value, param)
                all_results[param_name] = results

        return all_results

    async def validate_async(self, param_set: ParameterSet) -> dict[str, List[ValidationResult]]:
        """Validate entire parameter set including async validators.

        Args:
            param_set: ParameterSet to validate.

        Returns:
            Dictionary mapping parameter names to validation results.
        """
        all_results: dict[str, List[ValidationResult]] = {}

        # Run all validations concurrently
        tasks = []
        param_names = []

        for param_name, param in param_set.parameters.items():
            if param_name in self.validators:
                tasks.append(self.validators[param_name].validate_async(param.value, param))
                param_names.append(param_name)

        results_list = await asyncio.gather(*tasks)

        for param_name, results in zip(param_names, results_list):
            all_results[param_name] = results

        return all_results

    def get_errors(self, results: dict[str, List[ValidationResult]]) -> dict[str, List[ValidationResult]]:
        """Filter results to only errors.

        Args:
            results: Validation results.

        Returns:
            Dictionary of parameters with errors.
        """
        errors: dict[str, List[ValidationResult]] = {}

        for param_name, param_results in results.items():
            error_results = [r for r in param_results if not r.is_valid and r.severity == ValidationSeverity.ERROR]
            if error_results:
                errors[param_name] = error_results

        return errors

    def get_warnings(self, results: dict[str, List[ValidationResult]]) -> dict[str, List[ValidationResult]]:
        """Filter results to only warnings.

        Args:
            results: Validation results.

        Returns:
            Dictionary of parameters with warnings.
        """
        warnings: dict[str, List[ValidationResult]] = {}

        for param_name, param_results in results.items():
            warning_results = [
                r for r in param_results if not r.is_valid and r.severity == ValidationSeverity.WARNING
            ]
            if warning_results:
                warnings[param_name] = warning_results

        return warnings
