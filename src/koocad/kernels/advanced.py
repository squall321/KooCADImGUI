"""
Advanced CAD operations: sweep, loft, pattern, shell, and draft.

This module extends the kernel abstraction with advanced modeling operations
commonly used in parametric CAD systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from koocad.kernels.base import Shape


class PatternType(Enum):
    """Pattern repetition types."""

    LINEAR_1D = "linear_1d"
    LINEAR_2D = "linear_2d"
    CIRCULAR = "circular"
    PATH = "path"


class OffsetDirection(Enum):
    """Offset direction for shell operations."""

    INSIDE = "inside"
    OUTSIDE = "outside"
    BOTH = "both"


@dataclass
class SweepProfile:
    """Profile configuration for sweep operations."""

    profile: Shape
    path: Optional[Shape] = None
    twist_angle: float = 0.0  # degrees
    scale_factor: float = 1.0
    keep_normal: bool = True


@dataclass
class LoftProfile:
    """Profile for loft operations."""

    profile: Shape
    position: float  # 0.0 to 1.0 along loft path
    twist_angle: float = 0.0
    scale_factor: float = 1.0


@dataclass
class PatternConfig:
    """Configuration for pattern operations."""

    pattern_type: PatternType
    count: int
    spacing: Optional[float] = None  # For linear patterns
    angle: Optional[float] = None  # For circular patterns
    axis: Optional[Tuple[float, float, float]] = None
    center: Optional[Tuple[float, float, float]] = None


class AdvancedCADOps(ABC):
    """Abstract interface for advanced CAD operations.

    This extends the base kernel with more sophisticated modeling operations.
    """

    @abstractmethod
    def sweep(
        self,
        profile: Shape,
        path: Shape,
        twist_angle: float = 0.0,
    ) -> Shape:
        """Sweep a profile along a path.

        Args:
            profile: 2D profile to sweep.
            path: 3D path to sweep along.
            twist_angle: Twist angle in degrees.

        Returns:
            Swept solid.
        """
        ...

    @abstractmethod
    def loft_multi(
        self,
        profiles: List[Shape],
        ruled: bool = False,
    ) -> Shape:
        """Create loft through multiple profiles.

        Args:
            profiles: List of profiles to loft through.
            ruled: If True, create ruled surface (straight lines between profiles).

        Returns:
            Lofted solid.
        """
        ...

    @abstractmethod
    def pattern_linear_1d(
        self,
        shape: Shape,
        direction: Tuple[float, float, float],
        count: int,
        spacing: float,
    ) -> Shape:
        """Create linear pattern in one direction.

        Args:
            shape: Shape to pattern.
            direction: Pattern direction vector.
            count: Number of instances.
            spacing: Distance between instances.

        Returns:
            Compound shape with all instances.
        """
        ...

    @abstractmethod
    def pattern_linear_2d(
        self,
        shape: Shape,
        dir1: Tuple[float, float, float],
        count1: int,
        spacing1: float,
        dir2: Tuple[float, float, float],
        count2: int,
        spacing2: float,
    ) -> Shape:
        """Create linear pattern in two directions.

        Args:
            shape: Shape to pattern.
            dir1: First direction vector.
            count1: Count in first direction.
            spacing1: Spacing in first direction.
            dir2: Second direction vector.
            count2: Count in second direction.
            spacing2: Spacing in second direction.

        Returns:
            Compound shape with all instances.
        """
        ...

    @abstractmethod
    def pattern_circular(
        self,
        shape: Shape,
        axis: Tuple[float, float, float],
        center: Tuple[float, float, float],
        count: int,
        angle: float = 360.0,
    ) -> Shape:
        """Create circular pattern around axis.

        Args:
            shape: Shape to pattern.
            axis: Rotation axis.
            center: Center of rotation.
            count: Number of instances.
            angle: Total angle to distribute instances (default: 360°).

        Returns:
            Compound shape with all instances.
        """
        ...

    @abstractmethod
    def shell(
        self,
        shape: Shape,
        thickness: float,
        faces_to_remove: Optional[List[any]] = None,
        direction: OffsetDirection = OffsetDirection.INSIDE,
    ) -> Shape:
        """Create hollow shell from solid.

        Args:
            shape: Solid to shell.
            thickness: Wall thickness.
            faces_to_remove: Faces to remove (creates opening).
            direction: Offset direction.

        Returns:
            Shelled solid.
        """
        ...

    @abstractmethod
    def offset(
        self,
        shape: Shape,
        distance: float,
        direction: OffsetDirection = OffsetDirection.OUTSIDE,
    ) -> Shape:
        """Create offset surface.

        Args:
            shape: Shape to offset.
            distance: Offset distance.
            direction: Offset direction.

        Returns:
            Offset shape.
        """
        ...

    @abstractmethod
    def draft(
        self,
        shape: Shape,
        angle: float,
        neutral_plane: Tuple[float, float, float, float],
        pull_direction: Tuple[float, float, float],
    ) -> Shape:
        """Apply draft angle for manufacturing.

        Args:
            shape: Shape to apply draft to.
            angle: Draft angle in degrees.
            neutral_plane: Neutral plane (a, b, c, d) in ax + by + cz + d = 0.
            pull_direction: Direction of draft.

        Returns:
            Shape with draft applied.
        """
        ...

    @abstractmethod
    def thicken(
        self,
        face: Shape,
        thickness: float,
        direction: OffsetDirection = OffsetDirection.BOTH,
    ) -> Shape:
        """Thicken a face into a solid.

        Args:
            face: Face to thicken.
            thickness: Thickness.
            direction: Thickening direction.

        Returns:
            Solid.
        """
        ...


class GeometryAnalysis(ABC):
    """Geometric analysis utilities."""

    @abstractmethod
    def compute_volume(self, shape: Shape) -> float:
        """Compute volume of solid."""
        ...

    @abstractmethod
    def compute_surface_area(self, shape: Shape) -> float:
        """Compute surface area."""
        ...

    @abstractmethod
    def compute_center_of_mass(self, shape: Shape) -> Tuple[float, float, float]:
        """Compute center of mass."""
        ...

    @abstractmethod
    def compute_moment_of_inertia(
        self,
        shape: Shape,
        density: float = 1.0,
    ) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Compute moment of inertia tensor.

        Args:
            shape: Shape to analyze.
            density: Material density.

        Returns:
            Tuple of (principal_moments, principal_axes).
        """
        ...

    @abstractmethod
    def check_self_intersection(self, shape: Shape) -> bool:
        """Check if shape has self-intersections.

        Returns:
            True if self-intersecting.
        """
        ...

    @abstractmethod
    def compute_clearance(
        self,
        shape1: Shape,
        shape2: Shape,
    ) -> float:
        """Compute minimum clearance between two shapes.

        Args:
            shape1: First shape.
            shape2: Second shape.

        Returns:
            Minimum distance (0 if touching, negative if intersecting).
        """
        ...

    @abstractmethod
    def check_collision(
        self,
        shape1: Shape,
        shape2: Shape,
        tolerance: float = 1e-6,
    ) -> bool:
        """Check if two shapes collide.

        Args:
            shape1: First shape.
            shape2: Second shape.
            tolerance: Collision tolerance.

        Returns:
            True if colliding.
        """
        ...
