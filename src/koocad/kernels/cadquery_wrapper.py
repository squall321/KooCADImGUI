"""
CadQuery kernel wrapper implementation.

This module wraps CadQuery to conform to the KooCAD kernel interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import cadquery as cq
import numpy as np
from numpy.typing import NDArray

from koocad.kernels.base import CADKernel, KernelFactory, KernelType, Shape, ShapeType


class CadQueryShape(Shape):
    """CadQuery shape wrapper."""

    def __init__(self, cq_object: cq.Workplane) -> None:
        """Initialize with CadQuery Workplane.

        Args:
            cq_object: CadQuery Workplane object.
        """
        super().__init__(cq_object)
        self._cq: cq.Workplane = cq_object

    @property
    def cq(self) -> cq.Workplane:
        """Get CadQuery workplane."""
        return self._cq

    def bounding_box(self) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Get bounding box."""
        bb = self._cq.val().BoundingBox()
        min_point = np.array([bb.xmin, bb.ymin, bb.zmin])
        max_point = np.array([bb.xmax, bb.ymax, bb.zmax])
        return min_point, max_point

    def center_of_mass(self) -> NDArray[np.float64]:
        """Get center of mass."""
        com = self._cq.val().Center()
        return np.array([com.x, com.y, com.z])

    def volume(self) -> float:
        """Get volume."""
        try:
            shape = self._cq.val()
            if hasattr(shape, "Volume"):
                return float(shape.Volume())
            return 0.0
        except Exception:
            return 0.0

    def area(self) -> float:
        """Get surface area."""
        try:
            shape = self._cq.val()
            if hasattr(shape, "Area"):
                return float(shape.Area())
            return 0.0
        except Exception:
            return 0.0

    def shape_type(self) -> ShapeType:
        """Get shape type."""
        shape = self._cq.val()
        shape_type_str = shape.ShapeType()

        type_mapping = {
            "Vertex": ShapeType.VERTEX,
            "Edge": ShapeType.EDGE,
            "Wire": ShapeType.WIRE,
            "Face": ShapeType.FACE,
            "Shell": ShapeType.SHELL,
            "Solid": ShapeType.SOLID,
            "Compound": ShapeType.COMPOUND,
        }

        return type_mapping.get(shape_type_str, ShapeType.COMPOUND)

    def translate(self, dx: float, dy: float, dz: float) -> CadQueryShape:
        """Translate shape."""
        translated = self._cq.translate((dx, dy, dz))
        return CadQueryShape(translated)

    def rotate(
        self,
        axis: Tuple[float, float, float],
        angle: float,
        center: Optional[Tuple[float, float, float]] = None,
    ) -> CadQueryShape:
        """Rotate shape."""
        center_point = center if center else (0, 0, 0)
        rotated = self._cq.rotate(center_point, center_point, angle)
        return CadQueryShape(rotated)

    def scale(self, sx: float, sy: float, sz: float) -> CadQueryShape:
        """Scale shape."""
        # CadQuery doesn't have direct scale, use transformation matrix
        scaled = self._cq.val().scale(sx, sy, sz)
        return CadQueryShape(cq.Workplane("XY").add(scaled))

    def mirror(self, plane: str = "XY") -> CadQueryShape:
        """Mirror shape."""
        mirrored = self._cq.mirror(mirrorPlane=plane)
        return CadQueryShape(mirrored)

    def union(self, other: Shape) -> CadQueryShape:
        """Boolean union."""
        if not isinstance(other, CadQueryShape):
            raise TypeError("Can only union with another CadQueryShape")

        result = self._cq.union(other.cq)
        return CadQueryShape(result)

    def intersect(self, other: Shape) -> CadQueryShape:
        """Boolean intersection."""
        if not isinstance(other, CadQueryShape):
            raise TypeError("Can only intersect with another CadQueryShape")

        result = self._cq.intersect(other.cq)
        return CadQueryShape(result)

    def subtract(self, other: Shape) -> CadQueryShape:
        """Boolean subtraction."""
        if not isinstance(other, CadQueryShape):
            raise TypeError("Can only subtract another CadQueryShape")

        result = self._cq.cut(other.cq)
        return CadQueryShape(result)

    def fillet(self, radius: float, edges: Optional[List[Any]] = None) -> CadQueryShape:
        """Apply fillet."""
        if edges is not None:
            # Fillet specific edges
            result = self._cq.edges(edges).fillet(radius)
        else:
            # Fillet all edges
            result = self._cq.edges().fillet(radius)

        return CadQueryShape(result)

    def chamfer(self, distance: float, edges: Optional[List[Any]] = None) -> CadQueryShape:
        """Apply chamfer."""
        if edges is not None:
            result = self._cq.edges(edges).chamfer(distance)
        else:
            result = self._cq.edges().chamfer(distance)

        return CadQueryShape(result)

    def export_step(self, file_path: Union[str, Path]) -> None:
        """Export to STEP."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cq.exporters.export(self._cq, str(path), cq.exporters.ExportTypes.STEP)

    def export_stl(self, file_path: Union[str, Path], resolution: float = 0.1) -> None:
        """Export to STL."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # CadQuery STL export
        cq.exporters.export(
            self._cq,
            str(path),
            cq.exporters.ExportTypes.STL,
            tolerance=resolution,
            angularTolerance=0.1,
        )

    def export_iges(self, file_path: Union[str, Path]) -> None:
        """Export to IGES."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # CadQuery doesn't directly support IGES, use STEP as fallback
        cq.exporters.export(self._cq, str(path), cq.exporters.ExportTypes.STEP)


class CadQueryKernel(CADKernel):
    """CadQuery kernel implementation."""

    def __init__(self) -> None:
        """Initialize CadQuery kernel."""
        self.workplane = cq.Workplane("XY")

    def box(
        self,
        width: float,
        height: float,
        depth: float,
        centered: bool = True,
    ) -> CadQueryShape:
        """Create box."""
        wp = cq.Workplane("XY")

        if centered:
            box = wp.box(width, height, depth)
        else:
            # Create box with corner at origin
            box = wp.center(width / 2, height / 2).box(width, height, depth).translate((0, 0, depth / 2))

        return CadQueryShape(box)

    def sphere(self, radius: float, center: Tuple[float, float, float] = (0, 0, 0)) -> CadQueryShape:
        """Create sphere."""
        wp = cq.Workplane("XY")
        sphere = wp.sphere(radius)

        if center != (0, 0, 0):
            sphere = sphere.translate(center)

        return CadQueryShape(sphere)

    def cylinder(
        self,
        radius: float,
        height: float,
        centered: bool = True,
    ) -> CadQueryShape:
        """Create cylinder."""
        wp = cq.Workplane("XY")

        if centered:
            cylinder = wp.cylinder(height, radius, centered=True)
        else:
            cylinder = wp.cylinder(height, radius, centered=False)

        return CadQueryShape(cylinder)

    def cone(
        self,
        radius1: float,
        radius2: float,
        height: float,
    ) -> CadQueryShape:
        """Create cone."""
        wp = cq.Workplane("XY")

        # Create cone using CadQuery's cone method
        if radius2 == 0:
            # True cone
            cone = wp.cone(radius1, radius2, height)
        else:
            # Frustum
            cone = wp.cone(radius1, radius2, height)

        return CadQueryShape(cone)

    def extrude(
        self,
        profile: Any,
        distance: float,
    ) -> CadQueryShape:
        """Extrude profile."""
        if isinstance(profile, cq.Workplane):
            extruded = profile.extrude(distance)
            return CadQueryShape(extruded)
        else:
            raise TypeError("Profile must be a CadQuery Workplane")

    def revolve(
        self,
        profile: Any,
        axis: Tuple[float, float, float] = (0, 0, 1),
        angle: float = 360.0,
    ) -> CadQueryShape:
        """Revolve profile."""
        if isinstance(profile, cq.Workplane):
            revolved = profile.revolve(angleDegrees=angle)
            return CadQueryShape(revolved)
        else:
            raise TypeError("Profile must be a CadQuery Workplane")

    def loft(self, profiles: List[Any]) -> CadQueryShape:
        """Loft through profiles."""
        # Extract workplanes
        wires = []
        for profile in profiles:
            if isinstance(profile, cq.Workplane):
                wires.append(profile.val())
            else:
                raise TypeError("All profiles must be CadQuery Workplanes")

        # Create loft
        wp = cq.Workplane("XY")
        lofted = wp.add(cq.Solid.makeLoft(wires))

        return CadQueryShape(lofted)

    def import_step(self, file_path: Union[str, Path]) -> CadQueryShape:
        """Import STEP file."""
        path = Path(file_path)
        imported = cq.importers.importStep(str(path))
        return CadQueryShape(imported)

    def import_stl(self, file_path: Union[str, Path]) -> CadQueryShape:
        """Import STL file."""
        # CadQuery doesn't directly support STL import
        # This would require additional mesh processing
        raise NotImplementedError("STL import not yet implemented for CadQuery")


# Register CadQuery kernel
KernelFactory.register(KernelType.CADQUERY, CadQueryKernel)
