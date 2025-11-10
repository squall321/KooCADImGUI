"""
Tests for component generators.
"""

from pathlib import Path

import pytest

from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, Unit
from koocad.generators.base import GenerationContext, SimpleBoxGenerator
from koocad.generators.bga import BGAGenerator, MLCCGenerator
from koocad.kernels.base import KernelFactory, KernelType


@pytest.fixture
def kernel():
    """Create kernel for testing."""
    return KernelFactory.create(KernelType.CADQUERY)


@pytest.fixture
def bga_parameters():
    """Create valid BGA parameters."""
    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=12.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=0.8, unit=Unit.MM))
    params.add(IntParameter(name="ball_rows", value=5))
    params.add(IntParameter(name="ball_cols", value=5))
    params.add(FloatParameter(name="ball_pitch", value=2.0, unit=Unit.MM))
    params.add(FloatParameter(name="ball_diameter", value=1.0, unit=Unit.MM))
    return params


@pytest.fixture
def mlcc_parameters():
    """Create valid MLCC parameters."""
    params = ParameterSet()
    params.add(FloatParameter(name="body_length", value=2.0, unit=Unit.MM))
    params.add(FloatParameter(name="body_width", value=1.25, unit=Unit.MM))
    params.add(FloatParameter(name="body_height", value=1.25, unit=Unit.MM))
    params.add(FloatParameter(name="termination_length", value=0.25, unit=Unit.MM))
    return params


def test_simple_box_generator(kernel):
    """Test simple box generator."""
    params = ParameterSet()
    params.add(FloatParameter(name="width", value=10.0))
    params.add(FloatParameter(name="height", value=20.0))
    params.add(FloatParameter(name="depth", value=30.0))

    generator = SimpleBoxGenerator(kernel=kernel)
    errors = generator.validate_parameters(params)
    assert len(errors) == 0

    context = GenerationContext(parameters=params)
    result = generator.generate(context)

    assert result.success
    assert result.shape is not None
    assert result.volume > 0


def test_bga_parameter_validation(kernel, bga_parameters):
    """Test BGA parameter validation."""
    generator = BGAGenerator(kernel=kernel)

    # Valid parameters
    errors = generator.validate_parameters(bga_parameters)
    assert len(errors) == 0

    # Missing parameters
    invalid_params = ParameterSet()
    errors = generator.validate_parameters(invalid_params)
    assert len(errors) > 0


def test_bga_generation(kernel, bga_parameters):
    """Test BGA generation."""
    generator = BGAGenerator(kernel=kernel)

    context = GenerationContext(
        parameters=bga_parameters,
        export_formats=[],  # Skip export for faster testing
    )

    result = generator.generate(context)

    assert result.success
    assert result.shape is not None
    assert result.volume > 0
    assert result.generation_time > 0

    # Check ball count in parameters
    params_used = result.parameters_used
    ball_count = params_used["ball_rows"] * params_used["ball_cols"]
    assert ball_count == 25  # 5x5


def test_bga_with_export(kernel, bga_parameters, tmp_path):
    """Test BGA generation with file export."""
    generator = BGAGenerator(kernel=kernel)

    context = GenerationContext(
        parameters=bga_parameters,
        output_dir=tmp_path,
        export_formats=["step", "stl"],
        mesh_resolution=0.1,
    )

    result = generator.generate(context)

    assert result.success
    assert "step" in result.exported_files
    assert "stl" in result.exported_files
    assert result.exported_files["step"].exists()
    assert result.exported_files["stl"].exists()


def test_bga_array_fits_substrate(kernel):
    """Test that BGA validation checks array fits on substrate."""
    # Create parameters where array is too large
    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=5.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=5.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=0.8, unit=Unit.MM))
    params.add(IntParameter(name="ball_rows", value=15))
    params.add(IntParameter(name="ball_cols", value=15))
    params.add(FloatParameter(name="ball_pitch", value=1.0, unit=Unit.MM))
    params.add(FloatParameter(name="ball_diameter", value=0.5, unit=Unit.MM))

    generator = BGAGenerator(kernel=kernel)
    errors = generator.validate_parameters(params)

    # Should have errors about array not fitting
    assert len(errors) > 0
    assert any("exceeds substrate" in err for err in errors)


def test_mlcc_generation(kernel, mlcc_parameters):
    """Test MLCC generation."""
    generator = MLCCGenerator(kernel=kernel)

    context = GenerationContext(
        parameters=mlcc_parameters,
        export_formats=[],
    )

    result = generator.generate(context)

    assert result.success
    assert result.shape is not None
    assert result.volume > 0


def test_mlcc_validation(kernel):
    """Test MLCC parameter validation."""
    generator = MLCCGenerator(kernel=kernel)

    # Missing parameters
    params = ParameterSet()
    errors = generator.validate_parameters(params)
    assert len(errors) > 0


def test_batch_generation(kernel, bga_parameters):
    """Test batch generation."""
    generator = BGAGenerator(kernel=kernel)

    # Create multiple contexts with different parameters
    contexts = []
    for pitch in [1.5, 2.0, 2.5]:
        params = ParameterSet()
        params.add(FloatParameter(name="substrate_width", value=12.0, unit=Unit.MM))
        params.add(FloatParameter(name="substrate_height", value=12.0, unit=Unit.MM))
        params.add(FloatParameter(name="substrate_thickness", value=0.8, unit=Unit.MM))
        params.add(IntParameter(name="ball_rows", value=5))
        params.add(IntParameter(name="ball_cols", value=5))
        params.add(FloatParameter(name="ball_pitch", value=pitch, unit=Unit.MM))
        params.add(FloatParameter(name="ball_diameter", value=pitch * 0.5, unit=Unit.MM))

        context = GenerationContext(
            parameters=params,
            export_formats=[],
        )
        contexts.append(context)

    results = generator.batch_generate(contexts)

    assert len(results) == 3
    assert all(r.success for r in results)
    assert all(r.volume > 0 for r in results)


def test_generation_metrics(kernel, bga_parameters):
    """Test that generation captures metrics."""
    generator = BGAGenerator(kernel=kernel)

    context = GenerationContext(
        parameters=bga_parameters,
        export_formats=[],
    )

    result = generator.generate(context)

    assert result.volume is not None
    assert result.volume > 0
    assert result.surface_area is not None
    assert result.surface_area > 0
    assert result.bounding_box is not None
    assert result.parameters_used is not None
    assert len(result.parameters_used) > 0


@pytest.mark.slow
def test_large_bga_generation(kernel):
    """Test generation of large BGA (slow test)."""
    params = ParameterSet()
    params.add(FloatParameter(name="substrate_width", value=20.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_height", value=20.0, unit=Unit.MM))
    params.add(FloatParameter(name="substrate_thickness", value=1.0, unit=Unit.MM))
    params.add(IntParameter(name="ball_rows", value=20))
    params.add(IntParameter(name="ball_cols", value=20))
    params.add(FloatParameter(name="ball_pitch", value=0.8, unit=Unit.MM))
    params.add(FloatParameter(name="ball_diameter", value=0.4, unit=Unit.MM))

    generator = BGAGenerator(kernel=kernel)
    context = GenerationContext(parameters=params, export_formats=[])

    result = generator.generate(context)

    assert result.success
    # 20x20 = 400 balls
    assert result.parameters_used["ball_rows"] * result.parameters_used["ball_cols"] == 400
