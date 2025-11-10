#!/usr/bin/env python
"""
Example demonstrating end-to-end CAD generation.

This example shows:
- Creating parametric BGA and MLCC models
- Using the kernel abstraction layer
- Exporting to STEP and STL formats
- Batch generation for parameter sweeps
"""

from pathlib import Path

from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, Unit
from koocad.core.presets import BGAPresets
from koocad.generators.base import GenerationContext
from koocad.generators.bga import BGAGenerator, MLCCGenerator
from koocad.kernels.base import KernelFactory, KernelType


def create_bga_parameters() -> ParameterSet:
    """Create BGA parameter set."""
    params = ParameterSet()

    params.add(
        FloatParameter(
            name="substrate_width",
            value=12.0,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="substrate_height",
            value=12.0,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="substrate_thickness",
            value=0.8,
            unit=Unit.MM,
        )
    )

    params.add(IntParameter(name="ball_rows", value=15))
    params.add(IntParameter(name="ball_cols", value=15))

    params.add(
        FloatParameter(
            name="ball_pitch",
            value=0.8,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="ball_diameter",
            value=0.4,
            unit=Unit.MM,
        )
    )

    return params


def create_mlcc_parameters() -> ParameterSet:
    """Create MLCC parameter set."""
    params = ParameterSet()

    params.add(
        FloatParameter(
            name="body_length",
            value=2.0,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="body_width",
            value=1.25,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="body_height",
            value=1.25,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="termination_length",
            value=0.25,
            unit=Unit.MM,
        )
    )

    return params


def main() -> None:
    """Run example."""
    print("=" * 60)
    print("CAD Generation Example")
    print("=" * 60)

    output_dir = Path("output/cad_models")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Example 1: Simple BGA generation
    print("\n1. Generating BGA package...")
    bga_params = create_bga_parameters()

    kernel = KernelFactory.create(KernelType.CADQUERY)
    bga_generator = BGAGenerator(kernel=kernel)

    # Validate parameters
    errors = bga_generator.validate_parameters(bga_params)
    if errors:
        print(f"   ✗ Validation errors: {errors}")
        return
    else:
        print("   ✓ Parameters validated")

    # Generate BGA
    context = GenerationContext(
        parameters=bga_params,
        output_dir=output_dir / "bga",
        export_formats=["step", "stl"],
        mesh_resolution=0.05,
    )

    result = bga_generator.generate(context)

    if result.success:
        print(f"   ✓ Generation successful in {result.generation_time:.2f}s")
        print(f"   Volume: {result.volume:.2f} mm³")
        print(f"   Surface area: {result.surface_area:.2f} mm²")
        print(f"   Ball count: {int(result.parameters_used['ball_rows'] * result.parameters_used['ball_cols'])}")

        for format_name, file_path in result.exported_files.items():
            print(f"   Exported {format_name.upper()}: {file_path}")
    else:
        print(f"   ✗ Generation failed: {result.errors}")
        return

    # Example 2: MLCC generation
    print("\n2. Generating MLCC capacitor...")
    mlcc_params = create_mlcc_parameters()
    mlcc_generator = MLCCGenerator(kernel=kernel)

    context = GenerationContext(
        parameters=mlcc_params,
        output_dir=output_dir / "mlcc",
        export_formats=["step"],
    )

    result = mlcc_generator.generate(context)

    if result.success:
        print(f"   ✓ Generation successful in {result.generation_time:.2f}s")
        print(f"   Volume: {result.volume:.2f} mm³")
        print(f"   Surface area: {result.surface_area:.2f} mm²")

        for format_name, file_path in result.exported_files.items():
            print(f"   Exported {format_name.upper()}: {file_path}")

    # Example 3: Using presets
    print("\n3. Generating BGA from JEDEC preset...")
    preset_params = BGAPresets.get("BGA_15x15_0.8mm")

    if preset_params:
        context = GenerationContext(
            parameters=preset_params,
            output_dir=output_dir / "bga_preset",
            export_formats=["step"],
        )

        result = bga_generator.generate(context)

        if result.success:
            print(f"   ✓ BGA (JEDEC 15x15, 0.8mm pitch) generated")
            print(f"   Generation time: {result.generation_time:.2f}s")
            print(f"   Output: {result.exported_files.get('step')}")

    # Example 4: Batch generation with parameter sweep
    print("\n4. Batch generation with parameter sweep...")
    contexts = []

    for pitch in [0.5, 0.65, 0.8, 1.0]:
        params = ParameterSet()
        params.add(FloatParameter(name="substrate_width", value=12.0, unit=Unit.MM))
        params.add(FloatParameter(name="substrate_height", value=12.0, unit=Unit.MM))
        params.add(FloatParameter(name="substrate_thickness", value=0.8, unit=Unit.MM))
        params.add(IntParameter(name="ball_rows", value=15))
        params.add(IntParameter(name="ball_cols", value=15))
        params.add(FloatParameter(name="ball_pitch", value=pitch, unit=Unit.MM))
        params.add(FloatParameter(name="ball_diameter", value=pitch * 0.5, unit=Unit.MM))

        context = GenerationContext(
            parameters=params,
            output_dir=output_dir / f"bga_pitch_{pitch}mm",
            export_formats=["step"],
        )
        contexts.append(context)

    results = bga_generator.batch_generate(contexts)

    success_count = sum(1 for r in results if r.success)
    total_time = sum(r.generation_time for r in results)

    print(f"   Generated {success_count}/{len(results)} models")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per model: {total_time / len(results):.2f}s")

    # Summary
    print("\n" + "=" * 60)
    print("Example complete!")
    print(f"Output directory: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
