"""
Meshing tools for FEM/CFD analysis.

Meshers:
    - Gmsh: Open-source 3D finite element mesh generator
    - Netgen: Automatic 3D tetrahedral mesh generator
    - LS-DYNA: Keyword file generator for explicit dynamics

Quality:
    - Mesh quality metrics (aspect ratio, Jacobian, warpage)
    - Adaptive refinement
    - Mesh conversion utilities
"""

from __future__ import annotations

try:
    from koocad.meshing.gmsh_mesher import GmshMesher
    from koocad.meshing.lsdyna import LSDYNAKeywordGenerator
    from koocad.meshing.quality import MeshQualityChecker
except ImportError:
    pass

__all__ = [
    "GmshMesher",
    "LSDYNAKeywordGenerator",
    "MeshQualityChecker",
]
