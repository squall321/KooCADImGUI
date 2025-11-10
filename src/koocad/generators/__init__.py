"""
Component generators for electronic parts.

This package provides generators that take parametric inputs and
produce 3D CAD models using the kernel abstraction layer.
"""

from koocad.generators.base import ComponentGenerator, GenerationContext, GenerationResult

__all__ = [
    "ComponentGenerator",
    "GenerationContext",
    "GenerationResult",
]
