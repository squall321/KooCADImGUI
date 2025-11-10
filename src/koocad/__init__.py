"""
KooCAD - Parametric Electronic Component CAD Automation System

A comprehensive framework for generating fully parametric 3D CAD models
of electronic components (BGA, WLP, passives) with HPC batch processing
and FEA meshing pipeline integration.
"""

__version__ = "0.1.0"
__author__ = "KooCAD Team"
__license__ = "MIT"

from koocad.core.parameters import Parameter, ParameterSet
from koocad.core.shape import Shape

__all__ = [
    "__version__",
    "Parameter",
    "ParameterSet",
    "Shape",
]
