"""
Parametric system core classes.

This module provides the foundation for the parametric engine, including
parameter types, constraints, and expression evaluation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class Unit(str, Enum):
    """Supported measurement units."""

    MM = "mm"
    INCH = "inch"
    MIL = "mil"
    UM = "um"
    CM = "cm"
    M = "m"


class Constraint(BaseModel):
    """Base class for parameter constraints."""

    type: str
    message: str = "Constraint violation"

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate value against constraint."""
        ...


class RangeConstraint(Constraint):
    """Min/max range constraint."""

    type: str = "range"
    min_value: float | None = None
    max_value: float | None = None

    def validate(self, value: float) -> bool:
        """Check if value is within range."""
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False
        return True


class Parameter(ABC, BaseModel, Generic[T]):
    """Base class for all parameter types."""

    name: str = Field(..., description="Parameter name")
    description: str = Field("", description="Human-readable description")
    value: T = Field(..., description="Current value")
    default_value: T | None = Field(None, description="Default value")
    unit: Unit | None = Field(None, description="Measurement unit")
    constraints: list[Constraint] = Field(
        default_factory=list, description="Validation constraints"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def validate_value(self, value: T) -> bool:
        """Validate value against all constraints."""
        for constraint in self.constraints:
            if not constraint.validate(value):
                raise ValueError(
                    f"Parameter '{self.name}' constraint violation: {constraint.message}"
                )
        return True

    @abstractmethod
    def to_base_unit(self) -> float:
        """Convert value to base unit (mm for length)."""
        ...


class FloatParameter(Parameter[float]):
    """Floating-point parameter with optional range constraints."""

    value: float
    min_value: float | None = None
    max_value: float | None = None
    step: float = 0.1

    def __init__(self, **data: Any):
        super().__init__(**data)
        # Auto-create range constraint if min/max specified
        if self.min_value is not None or self.max_value is not None:
            self.constraints.append(
                RangeConstraint(
                    min_value=self.min_value,
                    max_value=self.max_value,
                    message=f"Value must be between {self.min_value} and {self.max_value}",
                )
            )

    def to_base_unit(self) -> float:
        """Convert to millimeters."""
        if self.unit is None or self.unit == Unit.MM:
            return self.value
        elif self.unit == Unit.INCH:
            return self.value * 25.4
        elif self.unit == Unit.MIL:
            return self.value * 0.0254
        elif self.unit == Unit.UM:
            return self.value * 0.001
        elif self.unit == Unit.CM:
            return self.value * 10.0
        elif self.unit == Unit.M:
            return self.value * 1000.0
        else:
            raise ValueError(f"Unknown unit: {self.unit}")


class IntParameter(Parameter[int]):
    """Integer parameter."""

    value: int
    min_value: int | None = None
    max_value: int | None = None
    step: int = 1

    def to_base_unit(self) -> float:
        """Return as float."""
        return float(self.value)


class BoolParameter(Parameter[bool]):
    """Boolean parameter."""

    value: bool

    def to_base_unit(self) -> float:
        """Return 1.0 or 0.0."""
        return 1.0 if self.value else 0.0


class StrParameter(Parameter[str]):
    """String parameter."""

    value: str
    max_length: int | None = None

    def to_base_unit(self) -> float:
        """Not applicable for strings."""
        raise NotImplementedError("String parameters cannot be converted to base unit")


class EnumParameter(Parameter[str]):
    """Enumerated choice parameter."""

    value: str
    choices: list[str] = Field(..., description="Valid choices")

    @field_validator("value")
    @classmethod
    def validate_choice(cls, v: str) -> str:
        """Ensure value is in choices.

        Note: Full validation happens in __init__ after all fields are set.
        """
        return v

    def __init__(self, **data: Any):
        """Initialize and validate choice."""
        super().__init__(**data)
        if self.value not in self.choices:
            raise ValueError(f"Value '{self.value}' not in choices: {self.choices}")

    def to_base_unit(self) -> float:
        """Return index of choice."""
        return float(self.choices.index(self.value))


class ExpressionParameter(Parameter[str]):
    """Parameter defined by mathematical expression.

    Example:
        ExpressionParameter(
            name="inner_width",
            value="outer_width - 2 * wall_thickness",
            dependencies=["outer_width", "wall_thickness"]
        )
    """

    value: str  # Expression string
    dependencies: list[str] = Field(
        default_factory=list, description="Parameter names this expression depends on"
    )
    compiled_expr: Any = Field(None, description="Compiled sympy expression")

    def evaluate(self, context: dict[str, float]) -> float:
        """Evaluate expression with given context.

        Args:
            context: Dictionary mapping parameter names to values.

        Returns:
            Evaluated result as float.

        Raises:
            ValueError: If dependencies are missing from context.
        """
        import sympy as sp

        # Check dependencies
        for dep in self.dependencies:
            if dep not in context:
                raise ValueError(f"Missing dependency '{dep}' for expression '{self.value}'")

        # Compile if not already
        if self.compiled_expr is None:
            self.compiled_expr = sp.sympify(self.value)

        # Substitute values
        result = self.compiled_expr.subs(context)

        return float(result)

    def to_base_unit(self) -> float:
        """Cannot convert without context."""
        raise NotImplementedError("Expression parameters require context to evaluate")


class ParameterSet(BaseModel):
    """Collection of parameters with dependency resolution."""

    parameters: dict[str, Parameter] = Field(
        default_factory=dict, description="Parameter name -> Parameter object"
    )
    version: int = Field(1, description="Version number for tracking changes")
    checksum: str | None = Field(None, description="SHA256 checksum of parameters")

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def add(self, param: Parameter) -> None:
        """Add parameter to set."""
        self.parameters[param.name] = param

    def get(self, name: str) -> Parameter | None:
        """Get parameter by name."""
        return self.parameters.get(name)

    def set_value(self, name: str, value: Any) -> None:
        """Set parameter value with validation."""
        param = self.get(name)
        if param is None:
            raise KeyError(f"Parameter '{name}' not found")

        param.validate_value(value)
        param.value = value

    def evaluate_all(self) -> dict[str, float]:
        """Evaluate all parameters to float values.

        Returns:
            Dictionary mapping parameter names to evaluated float values.

        Raises:
            ValueError: If circular dependencies detected.
        """
        context: dict[str, float] = {}

        # First pass: evaluate non-expression parameters
        for name, param in self.parameters.items():
            if not isinstance(param, ExpressionParameter):
                context[name] = param.to_base_unit()

        # Second pass: evaluate expression parameters (topological sort)
        remaining = [p for p in self.parameters.values() if isinstance(p, ExpressionParameter)]
        max_iterations = len(remaining) + 1
        iterations = 0

        while remaining and iterations < max_iterations:
            made_progress = False

            for param in remaining[:]:
                if isinstance(param, ExpressionParameter):
                    # Check if all dependencies resolved
                    if all(dep in context for dep in param.dependencies):
                        context[param.name] = param.evaluate(context)
                        remaining.remove(param)
                        made_progress = True

            if not made_progress:
                # Circular dependency detected
                raise ValueError(
                    f"Circular dependency detected in expressions: "
                    f"{[p.name for p in remaining]}"
                )

            iterations += 1

        return context

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "parameters": {name: param.dict() for name, param in self.parameters.items()},
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParameterSet:
        """Deserialize from dictionary."""
        param_set = cls(version=data.get("version", 1))

        for name, param_data in data.get("parameters", {}).items():
            # Reconstruct parameter based on type
            param_type = param_data.get("__type__", "float")

            if param_type == "float":
                param = FloatParameter(**param_data)
            elif param_type == "int":
                param = IntParameter(**param_data)
            elif param_type == "bool":
                param = BoolParameter(**param_data)
            elif param_type == "str":
                param = StrParameter(**param_data)
            elif param_type == "enum":
                param = EnumParameter(**param_data)
            elif param_type == "expression":
                param = ExpressionParameter(**param_data)
            else:
                raise ValueError(f"Unknown parameter type: {param_type}")

            param_set.add(param)

        return param_set

    def compute_checksum(self) -> str:
        """Compute SHA256 checksum of parameter values."""
        import hashlib
        import json

        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()


# Aliases for compatibility
StringParameter = StrParameter
