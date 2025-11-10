#!/usr/bin/env python
"""
Example demonstrating advanced packaging features.

This example shows:
- Multilayer BGA with visible layer stackup
- Fan-out BGA with routing traces
- Wirebond packages with wire loops
- Flip-chip with C4 bumps and copper pillars
- Wafer Level Package (WLP) with RDL
"""

from pathlib import Path

from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, StrParameter, Unit
from koocad.generators.advanced_bga import (
    FanOutBGAGenerator,
    FlipChipBumpGenerator,
    MultilayerBGAGenerator,
    WirebondPackageGenerator,
    WLPGenerator,
)
from koocad.generators.base import GenerationContext


def generate_multilayer_bga():
    """Generate multilayer BGA example."""
    print("\n1. Generating Multilayer BGA (4-layer substrate)...")

    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=15.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=15.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=1.2, unit=Unit.MM))
    params.add(IntParameter(name="ball_rows", value=15))
    params.add(IntParameter(name="ball_cols", value=15))
    params.add(FloatParameter(name="ball_pitch", value=0.8, unit=Unit.MM))
    params.add(FloatParameter(name="ball_diameter", value=0.4, unit=Unit.MM))
    params.add(IntParameter(name="layer_count", value=4))

    generator = MultilayerBGAGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced_packaging/multilayer_bga"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Layers: {int(result.parameters_used['layer_count'])}")
        print(f"   Ball count: {int(result.parameters_used['ball_rows'] * result.parameters_used['ball_cols'])}")
    else:
        print(f"   ✗ Failed: {result.errors}")


def generate_fanout_bga():
    """Generate fan-out BGA example."""
    print("\n2. Generating Fan-out BGA with routing traces...")

    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=0.8, unit=Unit.MM))
    params.add(FloatParameter(name="ball_pitch", value=0.5, unit=Unit.MM))
    params.add(FloatParameter(name="ball_diameter", value=0.25, unit=Unit.MM))
    params.add(IntParameter(name="fanout_layers", value=2))

    generator = FanOutBGAGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced_packaging/fanout_bga"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Fan-out layers: {int(result.parameters_used['fanout_layers'])}")


def generate_wirebond_package():
    """Generate wirebond package example."""
    print("\n3. Generating Wirebond Package...")

    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=10.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=10.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=0.5, unit=Unit.MM))
    params.add(FloatParameter(name="die_width", value=5.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_height", value=5.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_thickness", value=0.3, unit=Unit.MM))
    params.add(FloatParameter(name="wire_diameter", value=0.025, unit=Unit.MM))
    params.add(FloatParameter(name="loop_height", value=0.3, unit=Unit.MM))
    params.add(IntParameter(name="bond_pad_count", value=16))

    generator = WirebondPackageGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced_packaging/wirebond"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Bond wires: {int(result.parameters_used['bond_pad_count'])}")
        print(f"   Wire diameter: {result.parameters_used['wire_diameter']:.3f} mm (25 µm)")


def generate_flipchip_c4():
    """Generate flip-chip with C4 bumps."""
    print("\n4. Generating Flip-Chip with C4 Bumps...")

    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=1.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_width", value=8.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_height", value=8.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_thickness", value=0.5, unit=Unit.MM))
    params.add(FloatParameter(name="bump_pitch", value=0.15, unit=Unit.MM))
    params.add(FloatParameter(name="bump_diameter", value=0.1, unit=Unit.MM))
    params.add(FloatParameter(name="bump_height", value=0.08, unit=Unit.MM))
    params.add(StrParameter(name="bump_type", value="c4"))

    generator = FlipChipBumpGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced_packaging/flipchip_c4"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Bump pitch: {result.parameters_used['bump_pitch']:.2f} mm (150 µm)")
        print(f"   Bump type: {result.parameters_used['bump_type']}")


def generate_flipchip_copper_pillar():
    """Generate flip-chip with copper pillars."""
    print("\n5. Generating Flip-Chip with Copper Pillars...")

    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=10.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=10.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=0.8, unit=Unit.MM))
    params.add(FloatParameter(name="die_width", value=6.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_height", value=6.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_thickness", value=0.4, unit=Unit.MM))
    params.add(FloatParameter(name="bump_pitch", value=0.1, unit=Unit.MM))
    params.add(FloatParameter(name="bump_diameter", value=0.05, unit=Unit.MM))
    params.add(FloatParameter(name="bump_height", value=0.06, unit=Unit.MM))
    params.add(StrParameter(name="bump_type", value="copper_pillar"))

    generator = FlipChipBumpGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced_packaging/flipchip_copper_pillar"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Bump pitch: {result.parameters_used['bump_pitch']:.2f} mm (100 µm)")


def generate_wlp():
    """Generate Wafer Level Package (WLP)."""
    print("\n6. Generating Wafer Level Package (WLP) with RDL...")

    params = ParameterSet()
    params.add(FloatParameter(name="die_width", value=3.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_height", value=3.0, unit=Unit.MM))
    params.add(FloatParameter(name="die_thickness", value=0.2, unit=Unit.MM))
    params.add(FloatParameter(name="bump_pitch", value=0.4, unit=Unit.MM))
    params.add(FloatParameter(name="bump_diameter", value=0.2, unit=Unit.MM))
    params.add(IntParameter(name="rdl_layers", value=2))

    generator = WLPGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced_packaging/wlp"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   RDL layers: {int(result.parameters_used['rdl_layers'])}")
        print(f"   Die size: {result.parameters_used['die_width']:.1f} x {result.parameters_used['die_height']:.1f} mm")


def main():
    """Run all advanced packaging examples."""
    print("=" * 70)
    print("Advanced Packaging Examples")
    print("=" * 70)

    try:
        # BGA variants
        generate_multilayer_bga()
        generate_fanout_bga()

        # Wire bonding
        generate_wirebond_package()

        # Flip-chip
        generate_flipchip_c4()
        generate_flipchip_copper_pillar()

        # WLP
        generate_wlp()

        print("\n" + "=" * 70)
        print("All advanced packaging examples completed!")
        print("Check output/advanced_packaging/ for generated STEP files")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Note: CadQuery must be installed to run these examples")
        print("Install with: pip install cadquery")


if __name__ == "__main__":
    main()
