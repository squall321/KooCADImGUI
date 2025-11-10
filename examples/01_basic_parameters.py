"""
Example 1: Basic Parameter Usage

This example demonstrates how to create and use various parameter types.
"""

from koocad.core.parameters import (
    BoolParameter,
    EnumParameter,
    ExpressionParameter,
    FloatParameter,
    IntParameter,
    ParameterSet,
    Unit,
)


def main() -> None:
    """Run basic parameter examples."""
    print("=" * 60)
    print("KooCAD - Basic Parameter Usage")
    print("=" * 60)

    # 1. Float parameter with units
    print("\n1. Float Parameter with Unit Conversion")
    print("-" * 40)

    substrate_width = FloatParameter(
        name="substrate_width",
        description="BGA substrate width",
        value=12.0,
        unit=Unit.MM,
        min_value=5.0,
        max_value=50.0,
    )

    print(f"Parameter: {substrate_width.name}")
    print(f"Value: {substrate_width.value} {substrate_width.unit}")
    print(f"In base unit (mm): {substrate_width.to_base_unit()}")

    # Convert to inches
    substrate_width_inch = FloatParameter(
        name="substrate_width_inch",
        value=0.5,
        unit=Unit.INCH,
    )
    print(f"\n0.5 inch = {substrate_width_inch.to_base_unit():.2f} mm")

    # 2. Integer parameter
    print("\n2. Integer Parameter")
    print("-" * 40)

    ball_count = IntParameter(
        name="ball_rows",
        description="Number of ball rows in BGA",
        value=15,
        min_value=2,
        max_value=50,
    )

    print(f"Parameter: {ball_count.name}")
    print(f"Value: {ball_count.value}")

    # 3. Enum parameter
    print("\n3. Enum Parameter")
    print("-" * 40)

    ball_pattern = EnumParameter(
        name="ball_pattern",
        description="BGA ball array pattern",
        value="full",
        choices=["full", "peripheral", "custom"],
    )

    print(f"Parameter: {ball_pattern.name}")
    print(f"Value: {ball_pattern.value}")
    print(f"Available choices: {ball_pattern.choices}")

    # 4. Boolean parameter
    print("\n4. Boolean Parameter")
    print("-" * 40)

    enable_soldermask = BoolParameter(
        name="enable_soldermask",
        description="Add soldermask layer",
        value=True,
    )

    print(f"Parameter: {enable_soldermask.name}")
    print(f"Value: {enable_soldermask.value}")

    # 5. Expression parameter
    print("\n5. Expression Parameter")
    print("-" * 40)

    inner_width = ExpressionParameter(
        name="inner_width",
        description="Inner cavity width",
        value="substrate_width - 2 * edge_margin",
        dependencies=["substrate_width", "edge_margin"],
    )

    # Evaluate with context
    context = {
        "substrate_width": 12.0,
        "edge_margin": 0.5,
    }

    result = inner_width.evaluate(context)
    print(f"Expression: {inner_width.value}")
    print(f"Dependencies: {inner_width.dependencies}")
    print(f"Context: {context}")
    print(f"Result: {result} mm")

    # 6. Parameter Set
    print("\n6. Parameter Set with Dependencies")
    print("-" * 40)

    param_set = ParameterSet()

    # Add base parameters
    param_set.add(FloatParameter(name="substrate_width", value=12.0))
    param_set.add(FloatParameter(name="substrate_height", value=12.0))
    param_set.add(FloatParameter(name="substrate_thickness", value=0.8))
    param_set.add(FloatParameter(name="ball_pitch", value=0.8))
    param_set.add(IntParameter(name="ball_rows", value=15))
    param_set.add(IntParameter(name="ball_cols", value=15))

    # Add derived parameters (expressions)
    param_set.add(
        ExpressionParameter(
            name="ball_count",
            value="ball_rows * ball_cols",
            dependencies=["ball_rows", "ball_cols"],
        )
    )

    param_set.add(
        ExpressionParameter(
            name="array_width",
            value="(ball_cols - 1) * ball_pitch",
            dependencies=["ball_cols", "ball_pitch"],
        )
    )

    # Evaluate all parameters
    result_dict = param_set.evaluate_all()

    print(f"Total parameters: {len(param_set.parameters)}")
    print("\nEvaluated values:")
    for name, value in sorted(result_dict.items()):
        print(f"  {name}: {value:.2f}")

    # 7. Checksum
    print("\n7. Parameter Set Checksum")
    print("-" * 40)

    checksum = param_set.compute_checksum()
    print(f"SHA256 checksum: {checksum[:16]}...")

    # Modify parameter and recompute
    param_set.set_value("substrate_width", 14.0)
    new_checksum = param_set.compute_checksum()
    print(f"After change:     {new_checksum[:16]}...")
    print(f"Checksums match: {checksum == new_checksum}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
