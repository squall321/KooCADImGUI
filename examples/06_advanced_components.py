#!/usr/bin/env python
"""
Example demonstrating advanced component generation.

This example shows:
- Inductor generation (chip, toroidal, wirewound, shielded)
- Connector generation (pin header, USB, RJ45)
- Advanced CAD operations (patterns, shell, etc.)
"""

from pathlib import Path

from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, StrParameter, Unit
from koocad.generators.base import GenerationContext
from koocad.generators.connector import PinHeaderGenerator, RJ45ConnectorGenerator, USBConnectorGenerator
from koocad.generators.inductor import (
    ChipInductorGenerator,
    ShieldedInductorGenerator,
    ToroidalInductorGenerator,
    WirewoundInductorGenerator,
)


def generate_chip_inductor():
    """Generate chip inductor example."""
    print("\n1. Generating Chip Inductor (0805 size)...")

    params = ParameterSet()
    params.add(FloatParameter(name="body_length", value=2.0, unit=Unit.MM))
    params.add(FloatParameter(name="body_width", value=1.25, unit=Unit.MM))
    params.add(FloatParameter(name="body_height", value=1.0, unit=Unit.MM))
    params.add(FloatParameter(name="termination_length", value=0.3, unit=Unit.MM))
    params.add(FloatParameter(name="termination_height", value=0.5, unit=Unit.MM))

    generator = ChipInductorGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/chip_inductor"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Volume: {result.volume:.2f} mm³")
        print(f"   Output: {result.exported_files.get('step')}")
    else:
        print(f"   ✗ Failed: {result.errors}")


def generate_toroidal_inductor():
    """Generate toroidal inductor example."""
    print("\n2. Generating Toroidal Inductor...")

    params = ParameterSet()
    params.add(FloatParameter(name="core_outer_diameter", value=10.0, unit=Unit.MM))
    params.add(FloatParameter(name="core_inner_diameter", value=5.0, unit=Unit.MM))
    params.add(FloatParameter(name="core_height", value=4.0, unit=Unit.MM))

    generator = ToroidalInductorGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/toroidal_inductor"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Volume: {result.volume:.2f} mm³")
        print(f"   Surface area: {result.surface_area:.2f} mm²")


def generate_wirewound_inductor():
    """Generate wirewound inductor example."""
    print("\n3. Generating Wirewound Power Inductor...")

    params = ParameterSet()
    params.add(FloatParameter(name="core_diameter", value=6.0, unit=Unit.MM))
    params.add(FloatParameter(name="core_height", value=8.0, unit=Unit.MM))
    params.add(FloatParameter(name="base_width", value=10.0, unit=Unit.MM))
    params.add(FloatParameter(name="base_length", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="base_thickness", value=2.0, unit=Unit.MM))
    params.add(FloatParameter(name="mounting_hole_diameter", value=1.5, unit=Unit.MM))
    params.add(FloatParameter(name="mounting_hole_offset", value=4.0, unit=Unit.MM))

    generator = WirewoundInductorGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/wirewound_inductor"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Volume: {result.volume:.2f} mm³")


def generate_shielded_inductor():
    """Generate shielded inductor example."""
    print("\n4. Generating Shielded Power Inductor...")

    params = ParameterSet()
    params.add(FloatParameter(name="body_width", value=7.0, unit=Unit.MM))
    params.add(FloatParameter(name="body_length", value=7.0, unit=Unit.MM))
    params.add(FloatParameter(name="body_height", value=4.5, unit=Unit.MM))
    params.add(FloatParameter(name="core_diameter", value=5.0, unit=Unit.MM))

    generator = ShieldedInductorGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/shielded_inductor"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")


def generate_pin_header():
    """Generate pin header connector example."""
    print("\n5. Generating Pin Header (2x10 pins)...")

    params = ParameterSet()
    params.add(IntParameter(name="pin_count", value=20))
    params.add(IntParameter(name="pin_rows", value=2))
    params.add(FloatParameter(name="pin_pitch", value=2.54, unit=Unit.MM))
    params.add(FloatParameter(name="pin_diameter", value=0.65, unit=Unit.MM))
    params.add(FloatParameter(name="pin_length", value=11.0, unit=Unit.MM))
    params.add(FloatParameter(name="housing_height", value=8.5, unit=Unit.MM))

    generator = PinHeaderGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/pin_header"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Total pins: {int(result.parameters_used['pin_count'])}")


def generate_usb_connector():
    """Generate USB connector example."""
    print("\n6. Generating USB Type-C Connector...")

    params = ParameterSet()
    params.add(StrParameter(name="connector_type", value="type_c"))
    params.add(FloatParameter(name="housing_length", value=8.5, unit=Unit.MM))
    params.add(FloatParameter(name="housing_width", value=7.5, unit=Unit.MM))
    params.add(FloatParameter(name="housing_height", value=3.2, unit=Unit.MM))

    generator = USBConnectorGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/usb_connector"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Type: {result.parameters_used['connector_type']}")


def generate_rj45_connector():
    """Generate RJ45 Ethernet connector example."""
    print("\n7. Generating RJ45 Ethernet Connector...")

    params = ParameterSet()
    params.add(FloatParameter(name="housing_width", value=15.6, unit=Unit.MM))
    params.add(FloatParameter(name="housing_height", value=21.0, unit=Unit.MM))
    params.add(FloatParameter(name="housing_depth", value=16.0, unit=Unit.MM))

    generator = RJ45ConnectorGenerator()
    context = GenerationContext(
        parameters=params,
        output_dir=Path("output/advanced/rj45_connector"),
        export_formats=["step"],
    )

    result = generator.generate(context)

    if result.success:
        print(f"   ✓ Generated in {result.generation_time:.2f}s")
        print(f"   Dimensions: {result.parameters_used['housing_width']:.1f} x "
              f"{result.parameters_used['housing_depth']:.1f} x "
              f"{result.parameters_used['housing_height']:.1f} mm")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Advanced Component Generation Examples")
    print("=" * 60)

    try:
        # Inductors
        generate_chip_inductor()
        generate_toroidal_inductor()
        generate_wirewound_inductor()
        generate_shielded_inductor()

        # Connectors
        generate_pin_header()
        generate_usb_connector()
        generate_rj45_connector()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("Check output/advanced/ for generated STEP files")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("Note: CadQuery must be installed to run these examples")
        print("Install with: pip install cadquery")


if __name__ == "__main__":
    main()
