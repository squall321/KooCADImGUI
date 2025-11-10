"""
Tests for CAD kernel abstraction layer.
"""

import pytest

from koocad.kernels.base import KernelFactory, KernelType
from koocad.kernels.cadquery_wrapper import CadQueryKernel, CadQueryShape


@pytest.fixture
def kernel():
    """Create CadQuery kernel for testing."""
    return CadQueryKernel()


def test_kernel_factory():
    """Test kernel factory."""
    kernel = KernelFactory.create(KernelType.CADQUERY)
    assert isinstance(kernel, CadQueryKernel)


def test_box_creation(kernel):
    """Test box primitive creation."""
    box = kernel.box(10.0, 20.0, 30.0, centered=True)
    assert isinstance(box, CadQueryShape)

    # Check volume (10 * 20 * 30 = 6000)
    volume = box.volume()
    assert abs(volume - 6000.0) < 1.0


def test_sphere_creation(kernel):
    """Test sphere primitive creation."""
    sphere = kernel.sphere(5.0)
    assert isinstance(sphere, CadQueryShape)

    # Check volume (4/3 * π * r³)
    expected_volume = (4.0 / 3.0) * 3.14159 * (5.0**3)
    volume = sphere.volume()
    assert abs(volume - expected_volume) < 10.0  # Allow some tolerance


def test_cylinder_creation(kernel):
    """Test cylinder primitive creation."""
    cylinder = kernel.cylinder(radius=5.0, height=10.0, centered=True)
    assert isinstance(cylinder, CadQueryShape)

    # Check volume (π * r² * h)
    expected_volume = 3.14159 * (5.0**2) * 10.0
    volume = cylinder.volume()
    assert abs(volume - expected_volume) < 10.0


def test_bounding_box(kernel):
    """Test bounding box calculation."""
    box = kernel.box(10.0, 20.0, 30.0, centered=True)
    min_point, max_point = box.bounding_box()

    assert min_point[0] < 0 and max_point[0] > 0
    assert min_point[1] < 0 and max_point[1] > 0
    assert min_point[2] < 0 and max_point[2] > 0


def test_translation(kernel):
    """Test shape translation."""
    box = kernel.box(10.0, 10.0, 10.0, centered=True)
    translated = box.translate(5.0, 0.0, 0.0)

    # Center of mass should have moved
    com_original = box.center_of_mass()
    com_translated = translated.center_of_mass()

    assert abs(com_translated[0] - com_original[0] - 5.0) < 0.1


def test_boolean_union(kernel):
    """Test boolean union operation."""
    box1 = kernel.box(10.0, 10.0, 10.0, centered=True)
    box2 = kernel.sphere(5.0)

    union = box1.union(box2)
    assert isinstance(union, CadQueryShape)

    # Union volume should be >= larger shape volume
    assert union.volume() >= max(box1.volume(), box2.volume())


def test_boolean_subtract(kernel):
    """Test boolean subtraction operation."""
    box = kernel.box(10.0, 10.0, 10.0, centered=True)
    sphere = kernel.sphere(3.0)

    result = box.subtract(sphere)
    assert isinstance(result, CadQueryShape)

    # Result volume should be less than box volume
    assert result.volume() < box.volume()


def test_export_step(kernel, tmp_path):
    """Test STEP file export."""
    box = kernel.box(10.0, 10.0, 10.0)
    step_file = tmp_path / "test.step"

    box.export_step(step_file)
    assert step_file.exists()


def test_export_stl(kernel, tmp_path):
    """Test STL file export."""
    box = kernel.box(10.0, 10.0, 10.0)
    stl_file = tmp_path / "test.stl"

    box.export_stl(stl_file, resolution=0.1)
    assert stl_file.exists()
