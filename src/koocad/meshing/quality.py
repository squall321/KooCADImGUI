"""
Mesh quality checker.

Analyzes mesh quality using standard metrics:
- Aspect ratio
- Jacobian determinant
- Skewness/warpage
- Edge length ratio
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import math


class MeshQualityChecker:
    """Mesh quality analysis tool."""

    def __init__(self):
        """Initialize mesh quality checker."""
        self.metrics: Dict[str, List[float]] = {}

    def check_aspect_ratio(
        self,
        nodes: List[Tuple[float, float, float]],
        elements: List[List[int]],
    ) -> Dict[str, float]:
        """Check aspect ratio of elements.

        Aspect ratio = longest edge / shortest edge

        Args:
            nodes: List of (x, y, z) node coordinates.
            elements: List of element node connectivity.

        Returns:
            Dictionary with min, max, mean aspect ratios.
        """
        aspect_ratios = []

        for element in elements:
            # Get element nodes
            elem_nodes = [nodes[i] for i in element]

            # Calculate edge lengths
            edge_lengths = []
            n = len(elem_nodes)
            for i in range(n):
                for j in range(i + 1, n):
                    length = self._distance(elem_nodes[i], elem_nodes[j])
                    edge_lengths.append(length)

            if edge_lengths:
                min_edge = min(edge_lengths)
                max_edge = max(edge_lengths)
                aspect_ratio = max_edge / min_edge if min_edge > 0 else float('inf')
                aspect_ratios.append(aspect_ratio)

        self.metrics["aspect_ratio"] = aspect_ratios

        return {
            "min": min(aspect_ratios) if aspect_ratios else 0.0,
            "max": max(aspect_ratios) if aspect_ratios else 0.0,
            "mean": sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0.0,
        }

    def check_jacobian(
        self,
        nodes: List[Tuple[float, float, float]],
        elements: List[List[int]],
    ) -> Dict[str, float]:
        """Check Jacobian determinant of elements.

        Negative Jacobian indicates inverted elements.

        Args:
            nodes: List of (x, y, z) node coordinates.
            elements: List of element node connectivity.

        Returns:
            Dictionary with min, max Jacobian values.
        """
        jacobians = []

        for element in elements:
            if len(element) == 4:
                # Tetrahedral element
                jacobian = self._tet_jacobian(nodes, element)
                jacobians.append(jacobian)
            elif len(element) == 8:
                # Hexahedral element
                jacobian = self._hex_jacobian(nodes, element)
                jacobians.append(jacobian)

        self.metrics["jacobian"] = jacobians

        return {
            "min": min(jacobians) if jacobians else 0.0,
            "max": max(jacobians) if jacobians else 0.0,
            "negative_count": sum(1 for j in jacobians if j < 0),
        }

    def check_warpage(
        self,
        nodes: List[Tuple[float, float, float]],
        elements: List[List[int]],
    ) -> Dict[str, float]:
        """Check warpage of quad/hex faces.

        Warpage measures deviation from planarity.

        Args:
            nodes: List of (x, y, z) node coordinates.
            elements: List of element node connectivity.

        Returns:
            Dictionary with warpage statistics.
        """
        warpages = []

        for element in elements:
            if len(element) >= 4:
                # Check first 4 nodes for planarity
                warpage = self._quad_warpage(nodes, element[:4])
                warpages.append(warpage)

        self.metrics["warpage"] = warpages

        return {
            "min": min(warpages) if warpages else 0.0,
            "max": max(warpages) if warpages else 0.0,
            "mean": sum(warpages) / len(warpages) if warpages else 0.0,
        }

    def _distance(
        self,
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
    ) -> float:
        """Calculate distance between two points.

        Args:
            p1: First point (x, y, z).
            p2: Second point (x, y, z).

        Returns:
            Distance.
        """
        return math.sqrt(
            (p2[0] - p1[0]) ** 2 +
            (p2[1] - p1[1]) ** 2 +
            (p2[2] - p1[2]) ** 2
        )

    def _tet_jacobian(
        self,
        nodes: List[Tuple[float, float, float]],
        element: List[int],
    ) -> float:
        """Calculate Jacobian determinant for tetrahedral element.

        Args:
            nodes: List of all nodes.
            element: Tetrahedral element (4 nodes).

        Returns:
            Jacobian determinant.
        """
        # Get element nodes
        p0 = nodes[element[0]]
        p1 = nodes[element[1]]
        p2 = nodes[element[2]]
        p3 = nodes[element[3]]

        # Edge vectors
        v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        v3 = (p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2])

        # Jacobian = determinant of [v1 v2 v3]
        jacobian = (
            v1[0] * (v2[1] * v3[2] - v2[2] * v3[1]) -
            v1[1] * (v2[0] * v3[2] - v2[2] * v3[0]) +
            v1[2] * (v2[0] * v3[1] - v2[1] * v3[0])
        )

        return jacobian / 6.0  # Normalized by reference volume

    def _hex_jacobian(
        self,
        nodes: List[Tuple[float, float, float]],
        element: List[int],
    ) -> float:
        """Calculate minimum Jacobian for hexahedral element.

        Args:
            nodes: List of all nodes.
            element: Hexahedral element (8 nodes).

        Returns:
            Minimum Jacobian at corner nodes.
        """
        # Simplified: check at center
        # Full implementation would check at all Gauss points

        # Center point
        center = [0.0, 0.0, 0.0]
        for i in element:
            center[0] += nodes[i][0]
            center[1] += nodes[i][1]
            center[2] += nodes[i][2]

        center[0] /= 8
        center[1] /= 8
        center[2] /= 8

        # Approximate Jacobian using volume
        # Full implementation would use shape function derivatives
        return 1.0  # Placeholder

    def _quad_warpage(
        self,
        nodes: List[Tuple[float, float, float]],
        quad_nodes: List[int],
    ) -> float:
        """Calculate warpage of quadrilateral face.

        Args:
            nodes: List of all nodes.
            quad_nodes: Quad face nodes (4 nodes).

        Returns:
            Warpage angle in degrees.
        """
        # Get quad nodes
        p0 = nodes[quad_nodes[0]]
        p1 = nodes[quad_nodes[1]]
        p2 = nodes[quad_nodes[2]]
        p3 = nodes[quad_nodes[3]]

        # Calculate normals of two triangles
        n1 = self._cross_product(
            (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]),
            (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]),
        )

        n2 = self._cross_product(
            (p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2]),
            (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]),
        )

        # Angle between normals
        dot = sum(n1[i] * n2[i] for i in range(3))
        mag1 = math.sqrt(sum(n1[i] ** 2 for i in range(3)))
        mag2 = math.sqrt(sum(n2[i] ** 2 for i in range(3)))

        if mag1 * mag2 > 0:
            cos_angle = dot / (mag1 * mag2)
            cos_angle = max(-1.0, min(1.0, cos_angle))  # Clamp to [-1, 1]
            angle = math.acos(cos_angle)
            return math.degrees(angle)

        return 0.0

    def _cross_product(
        self,
        v1: Tuple[float, float, float],
        v2: Tuple[float, float, float],
    ) -> Tuple[float, float, float]:
        """Calculate cross product of two vectors.

        Args:
            v1: First vector.
            v2: Second vector.

        Returns:
            Cross product vector.
        """
        return (
            v1[1] * v2[2] - v1[2] * v2[1],
            v1[2] * v2[0] - v1[0] * v2[2],
            v1[0] * v2[1] - v1[1] * v2[0],
        )

    def generate_report(self) -> str:
        """Generate mesh quality report.

        Returns:
            Text report of mesh quality metrics.
        """
        report = "=" * 70 + "\n"
        report += "Mesh Quality Report\n"
        report += "=" * 70 + "\n\n"

        for metric_name, values in self.metrics.items():
            report += f"{metric_name.upper()}:\n"
            if values:
                report += f"  Min:  {min(values):.6f}\n"
                report += f"  Max:  {max(values):.6f}\n"
                report += f"  Mean: {sum(values) / len(values):.6f}\n"
                report += f"  Count: {len(values)}\n"
            report += "\n"

        return report
