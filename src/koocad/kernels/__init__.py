"""
CAD kernel integration layer.

This package provides abstraction over multiple CAD kernels:
- CadQuery (Python-based, built on OCCT)
- Direct OCCT C++ (via pybind11)
- Future: Other kernels as needed

The abstraction allows switching between kernels while maintaining
a consistent API.
"""

from koocad.kernels.base import CADKernel, KernelType, Shape
from koocad.kernels.cadquery_wrapper import CadQueryKernel

__all__ = [
    "Shape",
    "CADKernel",
    "KernelType",
    "CadQueryKernel",
]
