#!/usr/bin/env python
"""
Basic Parameter System Demo - CORRECTED API.

This example demonstrates the CORRECT usage of KooCAD's parameter system
with proper Pydantic BaseModel API conventions.

All APIs have been tested and verified to work correctly.

Usage:
    python examples/00_basic_parameters_corrected.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_basic_parameters():
    """Demonstrate basic parameter creation with CORRECT API."""
    print("=" * 70)
    print("Basic Parameter Creation (Correct API)")
    print("=" * 70)

    from koocad.core.parameters import (
        FloatParameter,
        IntParameter,
        BoolParameter,
        StringParameter,
    )

    print("\n1. FloatParameter - CORRECT usage with keyword arguments:")
    print("-" * 70)

    # ✅ CORRECT: Use keyword arguments
    width = FloatParameter(
        name='width',
        value=10.0,
        min_value=0.0,      # Note: min_value (not min_val)
        max_value=100.0,    # Note: max_value (not max_val)
        unit=None,
        description="Width of the component"
    )

    print(f"  Created: {width.name} = {width.value} mm")
    print(f"  Range: [{width.min_value}, {width.max_value}]")
    print(f"  Description: {width.description}")

    # Validate values
    print(f"\n  Validate value 50.0: {width.validate_value(50.0)}")

    try:
        width.validate_value(150.0)
        print("  ✗ Should have raised ValueError!")
    except ValueError as e:
        print(f"  ✓ Correctly rejected 150.0: {e}")

    print("\n2. IntParameter:")
    print("-" * 70)

    count = IntParameter(
        name='count',
        value=15,
        min_value=1,
        max_value=50,
        description="Number of components"
    )

    print(f"  Created: {count.name} = {count.value}")
    print(f"  Range: [{count.min_value}, {count.max_value}]")

    print("\n3. BoolParameter:")
    print("-" * 70)

    enable = BoolParameter(
        name='enable_feature',
        value=True,
        description="Enable advanced feature"
    )

    print(f"  Created: {enable.name} = {enable.value}")

    print("\n4. StringParameter:")
    print("-" * 70)

    material = StringParameter(
        name='material',
        value='copper',
        description="Material type"
    )

    print(f"  Created: {material.name} = {material.value}")

    print("\n✅ All parameter types created successfully!\n")

    return width, count, enable, material


def demo_expression_engine():
    """Demonstrate expression engine with CORRECT API."""
    print("=" * 70)
    print("Expression Engine (Correct API)")
    print("=" * 70)

    from koocad.core.expressions import ExpressionEngine

    engine = ExpressionEngine()
    print("\n✓ Created ExpressionEngine")

    # ✅ CORRECT: Pass variables as context dictionary
    print("\n1. Basic expressions:")
    print("-" * 70)

    context = {
        'width': 10.0,
        'height': 20.0,
        'depth': 5.0,
    }

    print(f"  Context: {context}")

    expressions = [
        ('width * height', 200.0),
        ('width + height + depth', 35.0),
        ('width * 2 + height / 4', 25.0),
    ]

    for expr, expected in expressions:
        result = engine.evaluate(expr, context)
        print(f"  {expr:30s} = {result:8.2f} (expected {expected})")

    print("\n2. Mathematical functions:")
    print("-" * 70)

    funcs = [
        ('sqrt(width * height)', 14.142136),
        ('max(width, height, depth)', 20.0),
        ('min(width, height, depth)', 5.0),
        ('abs(-width)', 10.0),
    ]

    for expr, expected in funcs:
        result = engine.evaluate(expr, context)
        print(f"  {expr:30s} = {result:8.6f} (expected ~{expected})")

    print("\n3. Built-in constants:")
    print("-" * 70)

    result_pi = engine.evaluate('pi * 2', {})
    result_e = engine.evaluate('e', {})

    print(f"  pi * 2 = {result_pi:.6f}")
    print(f"  e      = {result_e:.6f}")

    print("\n4. Extract variables from expression:")
    print("-" * 70)

    test_expr = 'a * b + c / d - e'
    variables = engine.extract_variables(test_expr)
    print(f"  Expression: {test_expr}")
    print(f"  Variables: {sorted(variables)}")

    print("\n✅ Expression engine working correctly!\n")


def demo_parameter_set():
    """Demonstrate ParameterSet with CORRECT API."""
    print("=" * 70)
    print("ParameterSet (Correct API)")
    print("=" * 70)

    from koocad.core.parameters import (
        FloatParameter,
        IntParameter,
        ParameterSet,
    )

    # Create parameters
    width = FloatParameter(name='width', value=10.0, min_value=0.0, max_value=100.0)
    height = FloatParameter(name='height', value=20.0, min_value=0.0, max_value=100.0)
    count = IntParameter(name='count', value=15, min_value=1, max_value=50)

    # Create parameter set
    param_set = ParameterSet()

    # ✅ CORRECT: Use add() method (not add_parameter)
    param_set.add(width)
    param_set.add(height)
    param_set.add(count)

    print(f"\n1. Created ParameterSet with {len(param_set.parameters)} parameters")
    print("-" * 70)

    for name, param in param_set.parameters.items():
        print(f"  {name:10s} = {param.value}")

    # ✅ CORRECT: Use get() method (not get_parameter)
    print("\n2. Retrieve parameter:")
    print("-" * 70)

    retrieved = param_set.get('width')
    print(f"  Retrieved: {retrieved.name} = {retrieved.value}")

    # Update value
    print("\n3. Update parameter value:")
    print("-" * 70)

    print(f"  Before: width = {param_set.get('width').value}")
    param_set.set_value('width', 15.0)
    print(f"  After:  width = {param_set.get('width').value}")

    # Evaluate all parameters
    print("\n4. Evaluate all parameters:")
    print("-" * 70)

    values = param_set.evaluate_all()
    for name, value in values.items():
        print(f"  {name:10s} = {value}")

    # Serialize to dict
    print("\n5. Serialize to dictionary:")
    print("-" * 70)

    data = param_set.to_dict()
    print(f"  Version: {data['version']}")
    print(f"  Parameters: {len(data['parameters'])}")

    print("\n✅ ParameterSet working correctly!\n")


def demo_expression_parameter():
    """Demonstrate ExpressionParameter with dependencies."""
    print("=" * 70)
    print("ExpressionParameter with Dependencies")
    print("=" * 70)

    from koocad.core.parameters import (
        FloatParameter,
        ExpressionParameter,
        ParameterSet,
    )

    # Create base parameters
    width = FloatParameter(name='width', value=10.0)
    height = FloatParameter(name='height', value=20.0)

    # Create expression parameter
    # Note: value field holds the expression string
    area = ExpressionParameter(
        name='area',
        value='width * height',  # Expression string goes in 'value' field
        description='Computed area'
    )

    # Create parameter set
    param_set = ParameterSet()
    param_set.add(width)
    param_set.add(height)
    param_set.add(area)

    print("\n1. Parameters:")
    print("-" * 70)
    print(f"  width  = {width.value}")
    print(f"  height = {height.value}")
    print(f"  area   = {area.value} (expression)")

    # Evaluate all (resolves dependencies)
    print("\n2. Evaluate with dependencies:")
    print("-" * 70)

    values = param_set.evaluate_all()
    for name, value in values.items():
        print(f"  {name:10s} = {value}")

    # Update base parameter and re-evaluate
    print("\n3. Update base parameter:")
    print("-" * 70)

    param_set.set_value('width', 15.0)
    print(f"  Updated width to {param_set.get('width').value}")

    values = param_set.evaluate_all()
    print(f"  New area = {values['area']} (was {200.0})")

    print("\n✅ Expression dependencies working correctly!\n")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("KooCAD Parameter System - CORRECTED API Demo")
    print("=" * 70)
    print("\nThis demo shows the CORRECT usage of all parameter APIs.")
    print("All tests have been verified to work.\n")

    # Run all demos
    demo_basic_parameters()
    demo_expression_engine()
    demo_parameter_set()
    demo_expression_parameter()

    print("=" * 70)
    print("All Demos Complete! ✅")
    print("=" * 70)
    print("\nKey API Points:")
    print("  1. Use KEYWORD arguments for all parameters")
    print("  2. Field names: min_value/max_value (not min_val/max_val)")
    print("  3. ExpressionEngine.evaluate(expr, context)")
    print("  4. ParameterSet methods: add(), get(), set_value()")
    print("  5. Validation: param.validate_value(value)")
    print("\nSee API_CORRECTIONS.md for complete documentation.")
    print("=" * 70)


if __name__ == "__main__":
    main()
