"""
IDE utilities for parametric CAD development.

This package provides tools for parameter inspection, visualization,
and performance profiling.
"""

from koocad.ide.inspector import ParameterInspector
from koocad.ide.visualizer import DependencyVisualizer
from koocad.ide.profiler import ExpressionProfiler

__all__ = [
    "ParameterInspector",
    "DependencyVisualizer",
    "ExpressionProfiler",
]
