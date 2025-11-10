"""
CadQuery implementation of advanced CAD operations.

This module extends CadQueryKernel with advanced modeling capabilities.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

try:
    import cadquery as cq
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
except ImportError:
    cq = None  # type: ignore
    BRepGProp = None  # type: ignore
    GProp_GProps = None  # type: ignore

from koocad.kernels.advanced import AdvancedCADOps, GeometryAnalysis, OffsetDirection
from koocad.kernels.base import Shape
from koocad.kernels.cadquery_wrapper import CadQueryKernel, CadQueryShape


class CadQueryAdvanced(CadQueryKernel, AdvancedCADOps, GeometryAnalysis):
    """CadQuery kernel with advanced operations."""

    def sweep(
        self,
        profile: Shape,
        path: Shape,
        twist_angle: float = 0.0,
    ) -> CadQueryShape:
        """Sweep profile along path."""
        if not isinstance(profile, CadQueryShape):
            raise TypeError("Profile must be CadQueryShape")

        if not isinstance(path, CadQueryShape):
            raise TypeError("Path must be CadQueryShape")

        # Get wire from path
        path_wire = path.cq.val()

        # Perform sweep
        swept = profile.cq.sweep(path_wire, multisection=False)

        # Apply twist if needed
        if twist_angle != 0:
            # CadQuery doesn't directly support twist in sweep
            # This would require custom OCCT code
            pass

        return CadQueryShape(swept)

    def loft_multi(
        self,
        profiles: List[Shape],
        ruled: bool = False,
    ) -> CadQueryShape:
        """Create loft through multiple profiles."""
        if not profiles:
            raise ValueError("Need at least one profile")

        # Extract wires from profiles
        wires = []
        for profile in profiles:
            if not isinstance(profile, CadQueryShape):
                raise TypeError("All profiles must be CadQueryShape")
            wires.append(profile.cq.val())

        # Create loft
        wp = cq.Workplane("XY")
        lofted = wp.add(cq.Solid.makeLoft(wires, ruled=ruled))

        return CadQueryShape(lofted)

    def pattern_linear_1d(
        self,
        shape: Shape,
        direction: Tuple[float, float, float],
        count: int,
        spacing: float,
    ) -> CadQueryShape:
        """Create 1D linear pattern."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        # Normalize direction
        import math

        length = math.sqrt(sum(d * d for d in direction))
        dir_norm = tuple(d / length for d in direction)

        # Create pattern
        result = shape.cq
        for i in range(1, count):
            offset = tuple(d * spacing * i for d in dir_norm)
            translated = shape.translate(offset[0], offset[1], offset[2])
            result = result.union(translated.cq)

        return CadQueryShape(result)

    def pattern_linear_2d(
        self,
        shape: Shape,
        dir1: Tuple[float, float, float],
        count1: int,
        spacing1: float,
        dir2: Tuple[float, float, float],
        count2: int,
        spacing2: float,
    ) -> CadQueryShape:
        """Create 2D linear pattern."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        import math

        # Normalize directions
        len1 = math.sqrt(sum(d * d for d in dir1))
        len2 = math.sqrt(sum(d * d for d in dir2))
        dir1_norm = tuple(d / len1 for d in dir1)
        dir2_norm = tuple(d / len2 for d in dir2)

        # Create 2D pattern
        result = shape.cq

        for i in range(count1):
            for j in range(count2):
                if i == 0 and j == 0:
                    continue  # Skip original

                offset = tuple(
                    dir1_norm[k] * spacing1 * i + dir2_norm[k] * spacing2 * j for k in range(3)
                )

                translated = shape.translate(offset[0], offset[1], offset[2])
                result = result.union(translated.cq)

        return CadQueryShape(result)

    def pattern_circular(
        self,
        shape: Shape,
        axis: Tuple[float, float, float],
        center: Tuple[float, float, float],
        count: int,
        angle: float = 360.0,
    ) -> CadQueryShape:
        """Create circular pattern."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        result = shape.cq
        angle_step = angle / count

        for i in range(1, count):
            rotation_angle = angle_step * i
            rotated = shape.rotate(axis, rotation_angle, center)
            result = result.union(rotated.cq)

        return CadQueryShape(result)

    def shell(
        self,
        shape: Shape,
        thickness: float,
        faces_to_remove: Optional[List[any]] = None,
        direction: OffsetDirection = OffsetDirection.INSIDE,
    ) -> CadQueryShape:
        """Create hollow shell."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        # CadQuery shell operation
        if faces_to_remove:
            # Select faces and shell
            shelled = shape.cq.faces().shell(thickness)
        else:
            # Shell all faces
            shelled = shape.cq.shell(thickness)

        return CadQueryShape(shelled)

    def offset(
        self,
        shape: Shape,
        distance: float,
        direction: OffsetDirection = OffsetDirection.OUTSIDE,
    ) -> CadQueryShape:
        """Create offset surface."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        # For 3D offset, we can use shell with appropriate thickness
        # Positive distance = outside, negative = inside
        actual_distance = distance if direction == OffsetDirection.OUTSIDE else -distance

        # This is simplified - real offset is more complex
        offset_shape = shape.cq.shell(actual_distance)

        return CadQueryShape(offset_shape)

    def draft(
        self,
        shape: Shape,
        angle: float,
        neutral_plane: Tuple[float, float, float, float],
        pull_direction: Tuple[float, float, float],
    ) -> CadQueryShape:
        """Apply draft angle."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        # CadQuery doesn't have direct draft support
        # Would need custom OCCT implementation
        # For now, return original shape
        # TODO: Implement in Phase 39
        return shape  # type: ignore

    def thicken(
        self,
        face: Shape,
        thickness: float,
        direction: OffsetDirection = OffsetDirection.BOTH,
    ) -> CadQueryShape:
        """Thicken face into solid."""
        if not isinstance(face, CadQueryShape):
            raise TypeError("Face must be CadQueryShape")

        # Use extrude for thickening
        if direction == OffsetDirection.BOTH:
            # Extrude in both directions
            thickened = face.cq.extrude(thickness / 2.0)
            thickened = thickened.translate(0, 0, -thickness / 4.0)
        elif direction == OffsetDirection.OUTSIDE:
            thickened = face.cq.extrude(thickness)
        else:  # INSIDE
            thickened = face.cq.extrude(-thickness)

        return CadQueryShape(thickened)

    # Geometry Analysis methods

    def compute_volume(self, shape: Shape) -> float:
        """Compute volume."""
        return shape.volume()

    def compute_surface_area(self, shape: Shape) -> float:
        """Compute surface area."""
        return shape.area()

    def compute_center_of_mass(self, shape: Shape) -> Tuple[float, float, float]:
        """Compute center of mass."""
        com = shape.center_of_mass()
        return (float(com[0]), float(com[1]), float(com[2]))

    def compute_moment_of_inertia(
        self,
        shape: Shape,
        density: float = 1.0,
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Compute moment of inertia tensor."""
        if not isinstance(shape, CadQueryShape):
            raise TypeError("Shape must be CadQueryShape")

        # This requires OCCT GProp calculations
        # Simplified implementation
        if BRepGProp is None or GProp_GProps is None:
            # Fallback: approximate using bounding box
            min_pt, max_pt = shape.bounding_box()
            dims = tuple(max_pt[i] - min_pt[i] for i in range(3))

            # Box approximation of moment of inertia
            mass = shape.volume() * density
            Ix = mass * (dims[1] ** 2 + dims[2] ** 2) / 12.0
            Iy = mass * (dims[0] ** 2 + dims[2] ** 2) / 12.0
            Iz = mass * (dims[0] ** 2 + dims[1] ** 2) / 12.0

            return ((Ix, Iy, Iz), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))

        # Full OCCT implementation
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(shape.cq.val().wrapped, props)

        # Get inertia matrix
        matrix = props.MatrixOfInertia()
        Ix = matrix.Value(0, 0)
        Iy = matrix.Value(1, 1)
        Iz = matrix.Value(2, 2)

        # Principal axes (simplified - identity for now)
        principal_axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))

        return ((Ix, Iy, Iz), principal_axes)

    def check_self_intersection(self, shape: Shape) -> bool:
        """Check for self-intersections."""
        # This requires BRepCheck from OCCT
        # Simplified: assume no self-intersection
        # TODO: Implement in Phase 50
        return False

    def compute_clearance(
        self,
        shape1: Shape,
        shape2: Shape,
    ) -> float:
        """Compute minimum clearance."""
        # Get bounding boxes for fast check
        bb1_min, bb1_max = shape1.bounding_box()
        bb2_min, bb2_max = shape2.bounding_box()

        # Compute distance between bounding box centers
        import math

        center1 = tuple((bb1_min[i] + bb1_max[i]) / 2.0 for i in range(3))
        center2 = tuple((bb2_min[i] + bb2_max[i]) / 2.0 for i in range(3))

        distance = math.sqrt(sum((center1[i] - center2[i]) ** 2 for i in range(3)))

        # Approximate clearance (should use BRepExtrema for precision)
        return distance

    def check_collision(
        self,
        shape1: Shape,
        shape2: Shape,
        tolerance: float = 1e-6,
    ) -> bool:
        """Check collision between shapes."""
        # Use bounding box for fast rejection
        bb1_min, bb1_max = shape1.bounding_box()
        bb2_min, bb2_max = shape2.bounding_box()

        # Check if bounding boxes overlap
        for i in range(3):
            if bb1_max[i] < bb2_min[i] - tolerance or bb2_max[i] < bb1_min[i] - tolerance:
                return False  # No collision

        # Bounding boxes overlap - could be colliding
        # For precise check, would need BRepAlgoAPI_Section
        # For now, assume collision if bounding boxes overlap
        return True
