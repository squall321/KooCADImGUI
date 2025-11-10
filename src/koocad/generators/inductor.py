"""
Inductor component generators.

This module generates various inductor types including wirewound,
chip inductors, and toroidal inductors.
"""

from __future__ import annotations

from typing import List

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class ChipInductorGenerator(ComponentGenerator):
    """Generator for chip (SMD) inductors.

    Chip inductors have a rectangular ceramic or ferrite body
    with wire windings and end terminations.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate chip inductor parameters.

        Required parameters:
        - body_length: Component length (mm)
        - body_width: Component width (mm)
        - body_height: Component height (mm)
        - termination_length: End termination length (mm)
        - termination_height: End termination height (mm)
        """
        errors = []

        required = [
            "body_length",
            "body_width",
            "body_height",
            "termination_length",
            "termination_height",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate chip inductor shape.

        Structure:
        1. Ceramic/ferrite body (rectangular)
        2. Two end terminations (electrodes)
        """
        params = context.parameters.evaluate_all()

        body_length = params["body_length"]
        body_width = params["body_width"]
        body_height = params["body_height"]
        term_length = params["termination_length"]
        term_height = params["termination_height"]

        # Create main body
        body = self.kernel.box(
            width=body_length - 2 * term_length,
            height=body_width,
            depth=body_height,
            centered=True,
        )

        # Create left termination
        left_term = self.kernel.box(
            width=term_length,
            height=body_width,
            depth=term_height,
            centered=False,
        )
        left_term = left_term.translate(
            -body_length / 2,
            -body_width / 2,
            -term_height / 2,
        )

        # Create right termination
        right_term = self.kernel.box(
            width=term_length,
            height=body_width,
            depth=term_height,
            centered=False,
        )
        right_term = right_term.translate(
            body_length / 2 - term_length,
            -body_width / 2,
            -term_height / 2,
        )

        # Combine all parts
        result = body.union(left_term).union(right_term)

        return result


class ToroidalInductorGenerator(ComponentGenerator):
    """Generator for toroidal (donut-shaped) inductors.

    Toroidal inductors have a toroidal core with wire windings.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate toroidal inductor parameters.

        Required parameters:
        - core_outer_diameter: Outer diameter of toroid (mm)
        - core_inner_diameter: Inner diameter (hole) of toroid (mm)
        - core_height: Height of toroid (mm)
        """
        errors = []

        required = [
            "core_outer_diameter",
            "core_inner_diameter",
            "core_height",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        # Validate constraints
        if not errors:
            values = params.evaluate_all()
            if values["core_inner_diameter"] >= values["core_outer_diameter"]:
                errors.append("Inner diameter must be less than outer diameter")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate toroidal inductor shape.

        The toroid is created by revolving a circle around an axis.
        """
        params = context.parameters.evaluate_all()

        outer_dia = params["core_outer_diameter"]
        inner_dia = params["core_inner_diameter"]
        height = params["core_height"]

        # Calculate torus parameters
        major_radius = (outer_dia + inner_dia) / 4.0  # Distance from center to tube center
        minor_radius = (outer_dia - inner_dia) / 4.0  # Tube radius

        # Create outer cylinder
        outer_cyl = self.kernel.cylinder(
            radius=outer_dia / 2.0,
            height=height,
            centered=True,
        )

        # Create inner cylinder (hole)
        inner_cyl = self.kernel.cylinder(
            radius=inner_dia / 2.0,
            height=height * 1.1,  # Slightly taller to ensure clean cut
            centered=True,
        )

        # Subtract inner from outer to create toroid
        toroid = outer_cyl.subtract(inner_cyl)

        return toroid


class WirewoundInductorGenerator(ComponentGenerator):
    """Generator for wirewound power inductors.

    These are larger inductors with visible wire windings,
    commonly used in power applications.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate wirewound inductor parameters.

        Required parameters:
        - core_diameter: Core diameter (mm)
        - core_height: Core height (mm)
        - base_width: Base plate width (mm)
        - base_length: Base plate length (mm)
        - base_thickness: Base plate thickness (mm)
        """
        errors = []

        required = [
            "core_diameter",
            "core_height",
            "base_width",
            "base_length",
            "base_thickness",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate wirewound inductor shape.

        Structure:
        1. Base plate with mounting holes
        2. Cylindrical ferrite core
        3. Wire winding (simplified as cylinder)
        """
        params = context.parameters.evaluate_all()

        core_dia = params["core_diameter"]
        core_height = params["core_height"]
        base_width = params["base_width"]
        base_length = params["base_length"]
        base_thickness = params["base_thickness"]

        # Create base plate
        base = self.kernel.box(
            width=base_length,
            height=base_width,
            depth=base_thickness,
            centered=True,
        )

        # Create ferrite core
        core = self.kernel.cylinder(
            radius=core_dia / 2.0,
            height=core_height,
            centered=False,
        )
        core = core.translate(0, 0, base_thickness / 2)

        # Combine base and core
        result = base.union(core)

        # Add mounting holes if parameters provided
        if "mounting_hole_diameter" in params:
            hole_dia = params["mounting_hole_diameter"]
            hole_offset = params.get("mounting_hole_offset", base_length * 0.35)

            # Create mounting hole
            hole = self.kernel.cylinder(
                radius=hole_dia / 2.0,
                height=base_thickness * 1.2,
                centered=True,
            )

            # Left hole
            left_hole = hole.translate(-hole_offset, 0, 0)
            result = result.subtract(left_hole)

            # Right hole
            right_hole = hole.translate(hole_offset, 0, 0)
            result = result.subtract(right_hole)

        return result


class ShieldedInductorGenerator(ComponentGenerator):
    """Generator for shielded power inductors.

    These inductors have a magnetic shield to reduce EMI.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate shielded inductor parameters.

        Required parameters:
        - body_width: Shield width (mm)
        - body_length: Shield length (mm)
        - body_height: Shield height (mm)
        - core_diameter: Internal core diameter (mm)
        """
        errors = []

        required = [
            "body_width",
            "body_length",
            "body_height",
            "core_diameter",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate shielded inductor shape.

        Structure:
        1. Outer shield (rectangular with rounded edges)
        2. Inner core (simplified as cylinder)
        """
        params = context.parameters.evaluate_all()

        width = params["body_width"]
        length = params["body_length"]
        height = params["body_height"]
        core_dia = params["core_diameter"]

        # Create outer shield
        shield = self.kernel.box(
            width=length,
            height=width,
            depth=height,
            centered=True,
        )

        # Apply fillet to edges for rounded appearance
        fillet_radius = min(width, length, height) * 0.1
        try:
            shield = shield.fillet(fillet_radius)
        except Exception:
            # Fillet might fail, continue without it
            pass

        # Create inner core cavity
        core = self.kernel.cylinder(
            radius=core_dia / 2.0,
            height=height * 0.8,
            centered=True,
        )

        # Subtract core from shield to show internal structure
        # (in reality, this would be filled, but we show cavity for visualization)
        # result = shield.subtract(core)

        # For simplicity, just return solid shield
        result = shield

        return result
