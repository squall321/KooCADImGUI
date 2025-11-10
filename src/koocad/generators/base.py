"""
Base classes for component generators.

This module defines the abstract interface for all component generators.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from koocad.core.parameters import ParameterSet
from koocad.kernels.base import CADKernel, KernelFactory, KernelType, Shape


@dataclass
class GenerationContext:
    """Context for CAD generation."""

    parameters: ParameterSet
    kernel_type: KernelType = KernelType.AUTO
    output_dir: Optional[Path] = None
    export_formats: List[str] = field(default_factory=lambda: ["step"])
    mesh_resolution: float = 0.1

    # Performance options
    use_cache: bool = True
    parallel: bool = False

    # Metadata
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of CAD generation."""

    shape: Shape
    parameters_used: Dict[str, float]
    generation_time: float
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Output files
    exported_files: Dict[str, Path] = field(default_factory=dict)

    # Metrics
    volume: Optional[float] = None
    surface_area: Optional[float] = None
    bounding_box: Optional[tuple] = None

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


class ComponentGenerator(ABC):
    """Abstract base class for component generators.

    Each generator creates a specific type of electronic component
    (e.g., BGA, MLCC, inductor) from parametric inputs.
    """

    def __init__(self, kernel: Optional[CADKernel] = None) -> None:
        """Initialize generator.

        Args:
            kernel: CAD kernel to use (default: auto-detect).
        """
        if kernel is None:
            kernel = KernelFactory.create(KernelType.AUTO)
        self.kernel = kernel

    @abstractmethod
    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate that parameters are suitable for generation.

        Args:
            params: Parameter set to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        ...

    @abstractmethod
    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate 3D shape from parameters.

        Args:
            context: Generation context with parameters and options.

        Returns:
            Generated shape.
        """
        ...

    def generate(self, context: GenerationContext) -> GenerationResult:
        """Full generation pipeline with validation and export.

        Args:
            context: Generation context.

        Returns:
            Generation result with shape and metadata.
        """
        start_time = datetime.now()

        # Validate parameters
        errors = self.validate_parameters(context.parameters)
        if errors:
            return GenerationResult(
                shape=None,  # type: ignore
                parameters_used={},
                generation_time=0.0,
                success=False,
                errors=errors,
            )

        try:
            # Generate shape
            shape = self.generate_shape(context)

            # Evaluate all parameters
            params_used = context.parameters.evaluate_all()

            # Compute metrics
            volume = shape.volume()
            surface_area = shape.area()
            bounding_box = shape.bounding_box()

            # Export if output directory provided
            exported_files = {}
            if context.output_dir:
                context.output_dir.mkdir(parents=True, exist_ok=True)

                for format_name in context.export_formats:
                    output_file = context.output_dir / f"model.{format_name}"

                    if format_name == "step":
                        shape.export_step(output_file)
                    elif format_name == "stl":
                        shape.export_stl(output_file, resolution=context.mesh_resolution)
                    elif format_name == "iges":
                        shape.export_iges(output_file)

                    exported_files[format_name] = output_file

            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()

            return GenerationResult(
                shape=shape,
                parameters_used=params_used,
                generation_time=generation_time,
                success=True,
                volume=volume,
                surface_area=surface_area,
                bounding_box=bounding_box,
                exported_files=exported_files,
            )

        except Exception as e:
            generation_time = (datetime.now() - start_time).total_seconds()
            return GenerationResult(
                shape=None,  # type: ignore
                parameters_used={},
                generation_time=generation_time,
                success=False,
                errors=[str(e)],
            )

    def batch_generate(
        self,
        contexts: List[GenerationContext],
        parallel: bool = False,
    ) -> List[GenerationResult]:
        """Generate multiple components in batch.

        Args:
            contexts: List of generation contexts.
            parallel: If True, use parallel processing.

        Returns:
            List of generation results.
        """
        results = []

        if parallel:
            # TODO: Implement parallel generation in Phase 136-145
            # For now, fall back to sequential
            pass

        # Sequential generation
        for context in contexts:
            result = self.generate(context)
            results.append(result)

        return results


class SimpleBoxGenerator(ComponentGenerator):
    """Simple box generator for testing purposes."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate box parameters."""
        errors = []

        required = ["width", "height", "depth"]
        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate box shape."""
        params = context.parameters.evaluate_all()

        width = params["width"]
        height = params["height"]
        depth = params["depth"]

        return self.kernel.box(width, height, depth, centered=True)
