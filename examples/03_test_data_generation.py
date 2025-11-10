"""
Example 3: Test Data Generation

This example demonstrates using factories to generate test data.
"""

from koocad.testing.factories import (
    BGAParameterFactory,
    MLCCParameterFactory,
    ParameterSweepFactory,
)


def main() -> None:
    """Run test data generation examples."""
    print("=" * 60)
    print("KooCAD - Test Data Generation")
    print("=" * 60)

    # Example 1: Generate BGA parameters
    print("\n1. Generate BGA Parameters")
    print("-" * 40)

    bga_params = BGAParameterFactory.create_basic()
    print(f"Generated BGA with {len(bga_params.parameters)} parameters:")

    for name, param in list(bga_params.parameters.items())[:5]:
        print(f"  - {name}: {param.value} {param.unit or ''}")

    # Example 2: BGA with expressions
    print("\n2. BGA with Expression Parameters")
    print("-" * 40)

    bga_with_expr = BGAParameterFactory.create_with_expressions()
    evaluated = bga_with_expr.evaluate_all()

    print("Evaluated parameters:")
    print(f"  - ball_rows: {evaluated['ball_rows']:.0f}")
    print(f"  - ball_cols: {evaluated['ball_cols']:.0f}")
    print(f"  - total_balls: {evaluated['total_balls']:.0f}")
    print(f"  - array_width: {evaluated['array_width']:.2f} mm")
    print(f"  - array_height: {evaluated['array_height']:.2f} mm")

    # Example 3: Generate MLCC parameters
    print("\n3. Generate MLCC Parameters")
    print("-" * 40)

    mlcc_params = MLCCParameterFactory.create_basic()
    mlcc_evaluated = mlcc_params.evaluate_all()

    print(f"MLCC Size: {mlcc_evaluated['body_length']:.2f} x "
          f"{mlcc_evaluated['body_width']:.2f} x "
          f"{mlcc_evaluated['body_height']:.2f} mm")
    print(f"Layers: {mlcc_evaluated['layer_count']:.0f}")
    print(f"Layer thickness: {mlcc_evaluated['layer_thickness']:.2f} µm")

    # Example 4: Batch generation
    print("\n4. Batch BGA Generation")
    print("-" * 40)

    batch = BGAParameterFactory.create_batch(count=5)
    print(f"Generated {len(batch)} BGA configurations:")

    for i, params in enumerate(batch, 1):
        evaluated = params.evaluate_all()
        print(f"  {i}. {evaluated['substrate_width']:.1f}mm x "
              f"{evaluated['substrate_height']:.1f}mm, "
              f"{evaluated['ball_rows']:.0f}x{evaluated['ball_cols']:.0f} balls")

    # Example 5: Cartesian parameter sweep
    print("\n5. Cartesian Parameter Sweep")
    print("-" * 40)

    param_ranges = {
        "substrate_width": [10.0, 12.0, 14.0],
        "ball_pitch": [0.5, 0.65, 0.8],
    }

    sweep = ParameterSweepFactory.create_cartesian_sweep(param_ranges)
    print(f"Generated {len(sweep)} parameter combinations:")

    for i, config in enumerate(sweep[:6], 1):  # Show first 6
        print(f"  {i}. width={config['substrate_width']}mm, "
              f"pitch={config['ball_pitch']}mm")

    if len(sweep) > 6:
        print(f"  ... and {len(sweep) - 6} more")

    # Example 6: Random parameter sweep
    print("\n6. Random Parameter Sweep (Monte Carlo)")
    print("-" * 40)

    param_ranges_random = {
        "substrate_width": (8.0, 20.0),
        "substrate_thickness": (0.5, 1.2),
    }

    random_sweep = ParameterSweepFactory.create_random_sweep(
        param_ranges_random,
        count=10,
    )

    print(f"Generated {len(random_sweep)} random parameter sets:")
    for i, config in enumerate(random_sweep[:5], 1):
        print(f"  {i}. width={config['substrate_width']:.2f}mm, "
              f"thickness={config['substrate_thickness']:.2f}mm")

    print(f"  ... and {len(random_sweep) - 5} more")

    # Example 7: Save parameter sweep to JSON
    print("\n7. Export Parameter Sweep")
    print("-" * 40)

    import json
    output_file = "data/param_sweep.json"

    try:
        with open(output_file, "w") as f:
            json.dump(sweep, f, indent=2)
        print(f"✓ Saved {len(sweep)} parameter sets to {output_file}")
    except Exception as e:
        print(f"⚠ Could not save file: {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
