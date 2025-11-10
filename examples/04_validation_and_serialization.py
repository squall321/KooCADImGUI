#!/usr/bin/env python
"""
Example demonstrating parameter validation and serialization.

This example shows:
- Parameter validation with validator chains
- Serialization to JSON and MessagePack
- Metadata and documentation generation
- IDE utilities (inspector, visualizer, profiler)
"""

from pathlib import Path

from koocad.core.metadata import DocumentationGenerator, MetadataRegistry, ParameterCategory, ParameterMetadata
from koocad.core.parameters import ExpressionParameter, FloatParameter, IntParameter, ParameterSet, Unit
from koocad.core.serialization import JSONSerializer, UniversalSerializer
from koocad.core.validation import ParameterSetValidator, RangeValidator, ValidationSeverity
from koocad.ide.inspector import ParameterInspector
from koocad.ide.profiler import ExpressionProfiler


def create_bga_parameters() -> ParameterSet:
    """Create BGA parameter set with validation."""
    params = ParameterSet()

    # Substrate dimensions
    params.add(
        FloatParameter(
            name="substrate_width",
            description="BGA substrate width",
            value=12.0,
            min_value=5.0,
            max_value=50.0,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="substrate_height",
            description="BGA substrate height",
            value=12.0,
            min_value=5.0,
            max_value=50.0,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="substrate_thickness",
            description="Substrate thickness",
            value=0.8,
            min_value=0.3,
            max_value=2.0,
            unit=Unit.MM,
        )
    )

    # Ball array
    params.add(
        IntParameter(
            name="ball_rows",
            description="Number of ball rows",
            value=15,
            min_value=2,
            max_value=50,
        )
    )

    params.add(
        IntParameter(
            name="ball_cols",
            description="Number of ball columns",
            value=15,
            min_value=2,
            max_value=50,
        )
    )

    params.add(
        FloatParameter(
            name="ball_pitch",
            description="Ball pitch (center-to-center)",
            value=0.8,
            min_value=0.4,
            max_value=1.27,
            unit=Unit.MM,
        )
    )

    params.add(
        FloatParameter(
            name="ball_diameter",
            description="Ball diameter",
            value=0.4,
            min_value=0.2,
            max_value=0.8,
            unit=Unit.MM,
        )
    )

    # Computed parameters
    params.add(
        ExpressionParameter(
            name="array_width",
            description="Total ball array width",
            value="(ball_cols - 1) * ball_pitch",
            dependencies=["ball_cols", "ball_pitch"],
        )
    )

    params.add(
        ExpressionParameter(
            name="array_height",
            description="Total ball array height",
            value="(ball_rows - 1) * ball_pitch",
            dependencies=["ball_rows", "ball_pitch"],
        )
    )

    params.add(
        ExpressionParameter(
            name="total_balls",
            description="Total number of balls",
            value="ball_rows * ball_cols",
            dependencies=["ball_rows", "ball_cols"],
        )
    )

    return params


def setup_validation(params: ParameterSet) -> ParameterSetValidator:
    """Setup validation rules."""
    validator = ParameterSetValidator()

    # Substrate dimensions validation
    validator.add_validator(
        "substrate_width",
        RangeValidator(min_value=5.0, max_value=50.0, severity=ValidationSeverity.ERROR),
    )

    validator.add_validator(
        "substrate_height",
        RangeValidator(min_value=5.0, max_value=50.0, severity=ValidationSeverity.ERROR),
    )

    # Ball diameter should be less than pitch
    from koocad.core.validation import FunctionValidator

    def ball_diameter_check(value: float) -> bool:
        """Check ball diameter is reasonable relative to pitch."""
        pitch = params.get("ball_pitch")
        if pitch is None:
            return True
        return value < pitch.value * 0.7

    validator.add_validator(
        "ball_diameter",
        FunctionValidator(
            func=ball_diameter_check,
            message="Ball diameter should be less than 70% of pitch",
            severity=ValidationSeverity.WARNING,
        ),
    )

    return validator


def setup_metadata(params: ParameterSet) -> MetadataRegistry:
    """Setup parameter metadata."""
    registry = MetadataRegistry()

    # Substrate width metadata
    registry.register(
        "substrate_width",
        ParameterMetadata(
            display_name="Substrate Width",
            description="Width of the BGA substrate in millimeters",
            category=ParameterCategory.GEOMETRY,
            tags={"substrate", "dimension", "bga"},
            tooltip="Overall substrate width including keepout zones",
            standard="JEDEC",
            ui_order=1,
            ui_group="Substrate",
            example_values=[10.0, 12.0, 14.0, 17.0],
        ),
    )

    # Ball pitch metadata
    registry.register(
        "ball_pitch",
        ParameterMetadata(
            display_name="Ball Pitch",
            description="Center-to-center distance between balls",
            category=ParameterCategory.GEOMETRY,
            tags={"ball", "pitch", "spacing"},
            tooltip="Standard pitches: 0.5mm, 0.65mm, 0.8mm, 1.0mm, 1.27mm",
            standard="JEDEC",
            reference="JESD95",
            ui_order=10,
            ui_group="Ball Array",
            example_values=[0.5, 0.65, 0.8, 1.0, 1.27],
        ),
    )

    # Total balls metadata
    registry.register(
        "total_balls",
        ParameterMetadata(
            display_name="Total Ball Count",
            description="Total number of solder balls in the array",
            category=ParameterCategory.GEOMETRY,
            tags={"ball", "count", "computed"},
            tooltip="Automatically computed from rows × columns",
            ui_order=99,
            ui_group="Ball Array",
            ui_readonly=True,
        ),
    )

    return registry


def main() -> None:
    """Run example."""
    print("=" * 60)
    print("Parameter Validation and Serialization Example")
    print("=" * 60)

    # Create parameters
    print("\n1. Creating BGA parameter set...")
    params = create_bga_parameters()
    print(f"   Created {len(params.parameters)} parameters")

    # Setup validation
    print("\n2. Setting up validation...")
    validator = setup_validation(params)
    results = validator.validate(params)

    errors = validator.get_errors(results)
    warnings = validator.get_warnings(results)

    print(f"   Validation complete: {len(errors)} errors, {len(warnings)} warnings")

    # Parameter inspection
    print("\n3. Inspecting parameters...")
    inspector = ParameterInspector(params)
    inspector.print_all_parameters(detailed=True)

    # Check for issues
    print("\n4. Checking for circular dependencies...")
    cycles = inspector.find_circular_dependencies()
    if cycles:
        print(f"   ⚠ Found {len(cycles)} circular dependencies!")
    else:
        print("   ✓ No circular dependencies detected")

    unused = inspector.find_unused_parameters()
    print(f"\n5. Unused parameters: {len(unused)}")
    if unused:
        print(f"   {', '.join(unused)}")

    # Profiling
    print("\n6. Profiling expression evaluation...")
    profiler = ExpressionProfiler(params)
    session = profiler.profile_all(iterations=1000)
    profiler.print_session(session, top_n=3)
    profiler.print_optimization_suggestions(session)

    # Serialization
    print("\n7. Serializing to JSON...")
    json_output = Path("output/bga_params.json")
    json_output.parent.mkdir(exist_ok=True)

    JSONSerializer.save(params, json_output)
    print(f"   Saved to: {json_output}")

    # Load and verify
    print("\n8. Loading from JSON...")
    loaded_params = JSONSerializer.load(json_output)
    print(f"   Loaded {len(loaded_params.parameters)} parameters")

    # Verify values match
    values_original = params.evaluate_all()
    values_loaded = loaded_params.evaluate_all()

    print("\n9. Verifying roundtrip...")
    all_match = all(abs(values_original[k] - values_loaded[k]) < 1e-9 for k in values_original.keys())
    print(f"   Roundtrip verification: {'✓ PASSED' if all_match else '✗ FAILED'}")

    # Metadata and documentation
    print("\n10. Generating documentation...")
    registry = setup_metadata(params)

    # Generate markdown
    markdown = DocumentationGenerator.generate_markdown(params, registry, title="BGA Parameters")
    markdown_path = Path("output/bga_params.md")
    markdown_path.write_text(markdown)
    print(f"   Markdown documentation: {markdown_path}")

    # Generate HTML
    html = DocumentationGenerator.generate_html(params, registry, title="BGA Parameters")
    html_path = Path("output/bga_params.html")
    html_path.write_text(html)
    print(f"   HTML documentation: {html_path}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
