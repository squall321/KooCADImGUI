"""
Base CAD kernel abstraction layer.

This module defines the abstract interface for CAD kernels and
shape operations. All kernel implementations must conform to this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import numpy as np
from numpy.typing import NDArray


class KernelType(Enum):
    """Supported CAD kernel types."""

    CADQUERY = "cadquery"
    OCCT = "occt"
    AUTO = "auto"  # Automatic selection


class ShapeType(Enum):
    """Types of geometric shapes."""

    VERTEX = "vertex"
    EDGE = "edge"
    WIRE = "wire"
    FACE = "face"
    SHELL = "shell"
    SOLID = "solid"
    COMPOUND = "compound"


class Shape(ABC):
    """Abstract base class for geometric shapes.

    This class provides a kernel-agnostic interface to 3D shapes.
    Each kernel implementation wraps its native shape type.
    """

    def __init__(self, native_shape: Any) -> None:
        """Initialize shape with native kernel object.

        Args:
            native_shape: Native shape object from underlying kernel.
        """
        self._native = native_shape

    @property
    def native(self) -> Any:
        """Get underlying native shape object."""
        return self._native

    @abstractmethod
    def bounding_box(self) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Get axis-aligned bounding box.

        Returns:
            Tuple of (min_point, max_point) as numpy arrays [x, y, z].
        """
        ...

    @abstractmethod
    def center_of_mass(self) -> NDArray[np.float64]:
        """Get center of mass.

        Returns:
            Center of mass as numpy array [x, y, z].
        """
        ...

    @abstractmethod
    def volume(self) -> float:
        """Get volume (for solids).

        Returns:
            Volume in cubic units, or 0.0 for non-solids.
        """
        ...

    @abstractmethod
    def area(self) -> float:
        """Get surface area.

        Returns:
            Surface area in square units.
        """
        ...

    @abstractmethod
    def shape_type(self) -> ShapeType:
        """Get shape type.

        Returns:
            ShapeType enum value.
        """
        ...

    @abstractmethod
    def translate(self, dx: float, dy: float, dz: float) -> Shape:
        """Translate shape by vector.

        Args:
            dx: Translation in X direction.
            dy: Translation in Y direction.
            dz: Translation in Z direction.

        Returns:
            New translated shape.
        """
        ...

    @abstractmethod
    def rotate(
        self,
        axis: Tuple[float, float, float],
        angle: float,
        center: Optional[Tuple[float, float, float]] = None,
    ) -> Shape:
        """Rotate shape around axis.

        Args:
            axis: Rotation axis as (x, y, z) tuple.
            angle: Rotation angle in degrees.
            center: Center of rotation (default: origin).

        Returns:
            New rotated shape.
        """
        ...

    @abstractmethod
    def scale(self, sx: float, sy: float, sz: float) -> Shape:
        """Scale shape by factors.

        Args:
            sx: Scale factor in X direction.
            sy: Scale factor in Y direction.
            sz: Scale factor in Z direction.

        Returns:
            New scaled shape.
        """
        ...

    @abstractmethod
    def mirror(self, plane: str = "XY") -> Shape:
        """Mirror shape across plane.

        Args:
            plane: Plane to mirror across ("XY", "YZ", "XZ").

        Returns:
            New mirrored shape.
        """
        ...

    # Boolean operations
    @abstractmethod
    def union(self, other: Shape) -> Shape:
        """Boolean union with another shape.

        Args:
            other: Shape to union with.

        Returns:
            Union result.
        """
        ...

    @abstractmethod
    def intersect(self, other: Shape) -> Shape:
        """Boolean intersection with another shape.

        Args:
            other: Shape to intersect with.

        Returns:
            Intersection result.
        """
        ...

    @abstractmethod
    def subtract(self, other: Shape) -> Shape:
        """Boolean subtraction (cut) another shape.

        Args:
            other: Shape to subtract.

        Returns:
            Subtraction result.
        """
        ...

    # Fillet and chamfer
    @abstractmethod
    def fillet(self, radius: float, edges: Optional[List[Any]] = None) -> Shape:
        """Apply fillet to edges.

        Args:
            radius: Fillet radius.
            edges: Specific edges to fillet (None = all edges).

        Returns:
            Filleted shape.
        """
        ...

    @abstractmethod
    def chamfer(self, distance: float, edges: Optional[List[Any]] = None) -> Shape:
        """Apply chamfer to edges.

        Args:
            distance: Chamfer distance.
            edges: Specific edges to chamfer (None = all edges).

        Returns:
            Chamfered shape.
        """
        ...

    # Export operations
    @abstractmethod
    def export_step(self, file_path: Union[str, Path]) -> None:
        """Export shape to STEP file.

        Args:
            file_path: Path to output STEP file.
        """
        ...

    @abstractmethod
    def export_stl(self, file_path: Union[str, Path], resolution: float = 0.1) -> None:
        """Export shape to STL file.

        Args:
            file_path: Path to output STL file.
            resolution: Mesh resolution (smaller = finer).
        """
        ...

    @abstractmethod
    def export_iges(self, file_path: Union[str, Path]) -> None:
        """Export shape to IGES file.

        Args:
            file_path: Path to output IGES file.
        """
        ...


class CADKernel(ABC):
    """Abstract base class for CAD kernel implementations.

    Each kernel provides methods to create primitive shapes and
    perform operations on them.
    """

    @abstractmethod
    def box(
        self,
        width: float,
        height: float,
        depth: float,
        centered: bool = True,
    ) -> Shape:
        """Create a box (rectangular prism).

        Args:
            width: Box width (X dimension).
            height: Box height (Y dimension).
            depth: Box depth (Z dimension).
            centered: If True, center at origin. If False, corner at origin.

        Returns:
            Box shape.
        """
        ...

    @abstractmethod
    def sphere(self, radius: float, center: Tuple[float, float, float] = (0, 0, 0)) -> Shape:
        """Create a sphere.

        Args:
            radius: Sphere radius.
            center: Center point as (x, y, z) tuple.

        Returns:
            Sphere shape.
        """
        ...

    @abstractmethod
    def cylinder(
        self,
        radius: float,
        height: float,
        centered: bool = True,
    ) -> Shape:
        """Create a cylinder.

        Args:
            radius: Cylinder radius.
            height: Cylinder height (Z direction).
            centered: If True, center at origin. If False, base at origin.

        Returns:
            Cylinder shape.
        """
        ...

    @abstractmethod
    def cone(
        self,
        radius1: float,
        radius2: float,
        height: float,
    ) -> Shape:
        """Create a cone (or frustum if radius2 > 0).

        Args:
            radius1: Base radius.
            radius2: Top radius.
            height: Cone height.

        Returns:
            Cone shape.
        """
        ...

    @abstractmethod
    def extrude(
        self,
        profile: Any,
        distance: float,
    ) -> Shape:
        """Extrude a 2D profile to create a 3D solid.

        Args:
            profile: 2D profile to extrude.
            distance: Extrusion distance.

        Returns:
            Extruded solid.
        """
        ...

    @abstractmethod
    def revolve(
        self,
        profile: Any,
        axis: Tuple[float, float, float] = (0, 0, 1),
        angle: float = 360.0,
    ) -> Shape:
        """Revolve a 2D profile around an axis.

        Args:
            profile: 2D profile to revolve.
            axis: Axis of revolution.
            angle: Revolution angle in degrees.

        Returns:
            Revolved solid.
        """
        ...

    @abstractmethod
    def loft(self, profiles: List[Any]) -> Shape:
        """Loft through multiple profiles.

        Args:
            profiles: List of 2D profiles to loft through.

        Returns:
            Lofted solid.
        """
        ...

    @abstractmethod
    def import_step(self, file_path: Union[str, Path]) -> Shape:
        """Import shape from STEP file.

        Args:
            file_path: Path to STEP file.

        Returns:
            Imported shape.
        """
        ...

    @abstractmethod
    def import_stl(self, file_path: Union[str, Path]) -> Shape:
        """Import shape from STL file.

        Args:
            file_path: Path to STL file.

        Returns:
            Imported shape.
        """
        ...


class KernelFactory:
    """Factory for creating CAD kernel instances."""

    _kernels: dict[KernelType, type[CADKernel]] = {}

    @classmethod
    def register(cls, kernel_type: KernelType, kernel_class: type[CADKernel]) -> None:
        """Register a kernel implementation.

        Args:
            kernel_type: Type of kernel.
            kernel_class: Kernel implementation class.
        """
        cls._kernels[kernel_type] = kernel_class

    @classmethod
    def create(cls, kernel_type: KernelType = KernelType.AUTO) -> CADKernel:
        """Create kernel instance.

        Args:
            kernel_type: Type of kernel to create.

        Returns:
            CAD kernel instance.

        Raises:
            ValueError: If kernel type is not registered.
        """
        if kernel_type == KernelType.AUTO:
            # Try CadQuery first, fallback to OCCT
            if KernelType.CADQUERY in cls._kernels:
                kernel_type = KernelType.CADQUERY
            elif KernelType.OCCT in cls._kernels:
                kernel_type = KernelType.OCCT
            else:
                raise ValueError("No CAD kernels registered")

        if kernel_type not in cls._kernels:
            raise ValueError(f"Kernel type '{kernel_type.value}' not registered")

        return cls._kernels[kernel_type]()
