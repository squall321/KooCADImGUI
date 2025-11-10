"""
CAD shape abstraction layer.

Provides a unified interface for working with CAD geometries from both
CadQuery and OCCT backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel


class BoundingBox(BaseModel):
    """Axis-aligned bounding box."""

    xmin: float
    ymin: float
    zmin: float
    xmax: float
    ymax: float
    zmax: float

    def center(self) -> tuple[float, float, float]:
        """Compute center point."""
        return (
            (self.xmin + self.xmax) / 2,
            (self.ymin + self.ymax) / 2,
            (self.zmin + self.zmax) / 2,
        )

    def size(self) -> tuple[float, float, float]:
        """Compute dimensions."""
        return (
            self.xmax - self.xmin,
            self.ymax - self.ymin,
            self.zmax - self.zmin,
        )


class Shape(ABC):
    """Abstract base class for CAD shapes.

    This class provides a unified interface for working with shapes from
    different CAD kernels (CadQuery, OCCT).
    """

    def __init__(self, wrapped: Any) -> None:
        """Initialize shape with underlying CAD object.

        Args:
            wrapped: The underlying CAD object (CQ Workplane, TopoDS_Shape, etc.)
        """
        self._wrapped = wrapped

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if shape is valid (no self-intersections, etc.)."""
        ...

    @abstractmethod
    def volume(self) -> float:
        """Compute volume in cubic millimeters."""
        ...

    @abstractmethod
    def surface_area(self) -> float:
        """Compute surface area in square millimeters."""
        ...

    @abstractmethod
    def bounding_box(self) -> BoundingBox:
        """Compute axis-aligned bounding box."""
        ...

    @abstractmethod
    def center_of_mass(self) -> tuple[float, float, float]:
        """Compute center of mass."""
        ...

    @abstractmethod
    def export_step(self, path: str | Path) -> None:
        """Export to STEP file format.

        Args:
            path: Output file path.
        """
        ...

    @abstractmethod
    def export_stl(
        self,
        path: str | Path,
        *,
        tolerance: float = 0.1,
        angular_tolerance: float = 0.1,
    ) -> None:
        """Export to STL file format.

        Args:
            path: Output file path.
            tolerance: Linear deflection tolerance (mm).
            angular_tolerance: Angular deflection tolerance (radians).
        """
        ...

    @abstractmethod
    def export_iges(self, path: str | Path) -> None:
        """Export to IGES file format.

        Args:
            path: Output file path.
        """
        ...

    def export_glb(
        self,
        path: str | Path,
        *,
        material: Optional[dict[str, Any]] = None,
    ) -> None:
        """Export to GLB/glTF 2.0 format.

        Args:
            path: Output file path.
            material: PBR material properties (optional).
        """
        raise NotImplementedError("GLB export not yet implemented")

    @abstractmethod
    def translate(self, dx: float, dy: float, dz: float) -> Shape:
        """Translate shape by offset.

        Args:
            dx: X offset (mm).
            dy: Y offset (mm).
            dz: Z offset (mm).

        Returns:
            New translated shape.
        """
        ...

    @abstractmethod
    def rotate(
        self,
        axis: tuple[float, float, float],
        angle: float,
        *,
        center: Optional[tuple[float, float, float]] = None,
    ) -> Shape:
        """Rotate shape around axis.

        Args:
            axis: Rotation axis vector.
            angle: Rotation angle (degrees).
            center: Rotation center (default: origin).

        Returns:
            New rotated shape.
        """
        ...

    @abstractmethod
    def mirror(
        self,
        plane_normal: tuple[float, float, float],
        *,
        plane_point: Optional[tuple[float, float, float]] = None,
    ) -> Shape:
        """Mirror shape across plane.

        Args:
            plane_normal: Plane normal vector.
            plane_point: Point on plane (default: origin).

        Returns:
            New mirrored shape.
        """
        ...

    @abstractmethod
    def union(self, *others: Shape) -> Shape:
        """Boolean union with other shapes.

        Args:
            others: Shapes to union with.

        Returns:
            New unioned shape.
        """
        ...

    @abstractmethod
    def intersect(self, *others: Shape) -> Shape:
        """Boolean intersection with other shapes.

        Args:
            others: Shapes to intersect with.

        Returns:
            New intersected shape.
        """
        ...

    @abstractmethod
    def subtract(self, *others: Shape) -> Shape:
        """Boolean subtraction of other shapes.

        Args:
            others: Shapes to subtract.

        Returns:
            New shape with others subtracted.
        """
        ...

    def __repr__(self) -> str:
        """String representation."""
        try:
            vol = self.volume()
            bbox = self.bounding_box()
            return f"<Shape volume={vol:.2f}mm³ bbox={bbox.size()}>"
        except Exception:
            return f"<Shape wrapped={type(self._wrapped).__name__}>"


class ShapeCollection:
    """Collection of multiple shapes (assembly)."""

    def __init__(self) -> None:
        """Initialize empty collection."""
        self.shapes: list[tuple[str, Shape]] = []

    def add(self, name: str, shape: Shape) -> None:
        """Add named shape to collection.

        Args:
            name: Component name.
            shape: CAD shape.
        """
        self.shapes.append((name, shape))

    def export_step(self, path: str | Path) -> None:
        """Export all shapes to single STEP assembly.

        Args:
            path: Output file path.
        """
        raise NotImplementedError("Assembly STEP export not yet implemented")

    def bounding_box(self) -> BoundingBox:
        """Compute bounding box of all shapes."""
        if not self.shapes:
            return BoundingBox(xmin=0, ymin=0, zmin=0, xmax=0, ymax=0, zmax=0)

        boxes = [shape.bounding_box() for _, shape in self.shapes]

        return BoundingBox(
            xmin=min(b.xmin for b in boxes),
            ymin=min(b.ymin for b in boxes),
            zmin=min(b.zmin for b in boxes),
            xmax=max(b.xmax for b in boxes),
            ymax=max(b.ymax for b in boxes),
            zmax=max(b.zmax for b in boxes),
        )
