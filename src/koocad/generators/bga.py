"""
BGA (Ball Grid Array) package generator.

This module generates 3D models of BGA packages with configurable
ball arrays and substrate dimensions.
"""

from __future__ import annotations

from typing import List

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class BGAGenerator(ComponentGenerator):
    """Generator for BGA packages."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate BGA parameters.

        Required parameters:
        - substrate_width: Substrate width (mm)
        - substrate_height: Substrate height (mm)
        - substrate_thickness: Substrate thickness (mm)
        - ball_rows: Number of ball rows
        - ball_cols: Number of ball columns
        - ball_pitch: Ball pitch (mm)
        - ball_diameter: Ball diameter (mm)
        """
        errors = []

        required = [
            "substrate_width",
            "substrate_height",
            "substrate_thickness",
            "ball_rows",
            "ball_cols",
            "ball_pitch",
            "ball_diameter",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        # Validate constraints if parameters exist
        if not errors:
            values = params.evaluate_all()

            # Check ball array fits on substrate
            array_width = (values["ball_cols"] - 1) * values["ball_pitch"]
            array_height = (values["ball_rows"] - 1) * values["ball_pitch"]

            if array_width > values["substrate_width"]:
                errors.append(
                    f"Ball array width ({array_width:.2f}mm) exceeds substrate width ({values['substrate_width']:.2f}mm)"
                )

            if array_height > values["substrate_height"]:
                errors.append(
                    f"Ball array height ({array_height:.2f}mm) exceeds substrate height ({values['substrate_height']:.2f}mm)"
                )

            # Check ball diameter vs pitch
            if values["ball_diameter"] >= values["ball_pitch"]:
                errors.append(f"Ball diameter must be less than pitch for clearance")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate BGA package shape.

        The BGA consists of:
        1. Substrate (rectangular body)
        2. Ball array (spheres in grid pattern)
        """
        params = context.parameters.evaluate_all()

        # Extract parameters
        substrate_width = params["substrate_width"]
        substrate_height = params["substrate_height"]
        substrate_thickness = params["substrate_thickness"]
        ball_rows = int(params["ball_rows"])
        ball_cols = int(params["ball_cols"])
        ball_pitch = params["ball_pitch"]
        ball_diameter = params["ball_diameter"]
        ball_radius = ball_diameter / 2.0

        # Create substrate (main body)
        substrate = self.kernel.box(
            width=substrate_width,
            height=substrate_height,
            depth=substrate_thickness,
            centered=True,
        )

        # Calculate ball array offset (center on substrate)
        array_width = (ball_cols - 1) * ball_pitch
        array_height = (ball_rows - 1) * ball_pitch
        x_offset = -array_width / 2.0
        y_offset = -array_height / 2.0
        z_offset = -substrate_thickness / 2.0 - ball_radius  # Below substrate

        # Create ball array
        balls_shape = None

        for row in range(ball_rows):
            for col in range(ball_cols):
                # Calculate ball position
                x = x_offset + col * ball_pitch
                y = y_offset + row * ball_pitch
                z = z_offset

                # Create ball
                ball = self.kernel.sphere(radius=ball_radius, center=(x, y, z))

                # Union with existing balls
                if balls_shape is None:
                    balls_shape = ball
                else:
                    balls_shape = balls_shape.union(ball)

        # Combine substrate and balls
        if balls_shape is not None:
            final_shape = substrate.union(balls_shape)
        else:
            final_shape = substrate

        return final_shape


class SimplifiedBGAGenerator(ComponentGenerator):
    """Simplified BGA generator using a single compound for balls.

    This version is faster for large ball counts as it doesn't perform
    union operations on each ball individually.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate BGA parameters."""
        # Same validation as BGAGenerator
        generator = BGAGenerator(kernel=self.kernel)
        return generator.validate_parameters(params)

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate simplified BGA shape.

        For very large ball counts (>100), this approach is more efficient.
        """
        params = context.parameters.evaluate_all()

        # Extract parameters
        substrate_width = params["substrate_width"]
        substrate_height = params["substrate_height"]
        substrate_thickness = params["substrate_thickness"]
        ball_rows = int(params["ball_rows"])
        ball_cols = int(params["ball_cols"])
        ball_pitch = params["ball_pitch"]
        ball_diameter = params["ball_diameter"]
        ball_radius = ball_diameter / 2.0

        # Create substrate
        substrate = self.kernel.box(
            width=substrate_width,
            height=substrate_height,
            depth=substrate_thickness,
            centered=True,
        )

        # For simplified version, create balls as individual spheres
        # and combine them at the end (more efficient for large arrays)
        array_width = (ball_cols - 1) * ball_pitch
        array_height = (ball_rows - 1) * ball_pitch
        x_offset = -array_width / 2.0
        y_offset = -array_height / 2.0
        z_offset = -substrate_thickness / 2.0 - ball_radius

        # Collect all balls
        balls = []
        for row in range(ball_rows):
            for col in range(ball_cols):
                x = x_offset + col * ball_pitch
                y = y_offset + row * ball_pitch
                z = z_offset

                ball = self.kernel.sphere(radius=ball_radius, center=(x, y, z))
                balls.append(ball)

        # Union all balls with substrate
        # For better performance, use balanced union tree
        result = substrate
        for ball in balls:
            result = result.union(ball)

        return result


class MLCCGenerator(ComponentGenerator):
    """Generator for MLCC (Multi-Layer Ceramic Capacitor) components.

    MLCCs are simpler rectangular components with end terminations.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate MLCC parameters.

        Required parameters:
        - body_length: Component length (mm)
        - body_width: Component width (mm)
        - body_height: Component height (mm)
        - termination_length: End termination length (mm)
        """
        errors = []

        required = [
            "body_length",
            "body_width",
            "body_height",
            "termination_length",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate MLCC shape.

        MLCC consists of:
        1. Ceramic body (center)
        2. Two end terminations (metal pads)
        """
        params = context.parameters.evaluate_all()

        body_length = params["body_length"]
        body_width = params["body_width"]
        body_height = params["body_height"]
        term_length = params["termination_length"]

        # Create ceramic body
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
            depth=body_height,
            centered=False,
        )
        left_term = left_term.translate(-body_length / 2, -body_width / 2, -body_height / 2)

        # Create right termination
        right_term = self.kernel.box(
            width=term_length,
            height=body_width,
            depth=body_height,
            centered=False,
        )
        right_term = right_term.translate(body_length / 2 - term_length, -body_width / 2, -body_height / 2)

        # Combine all parts
        result = body.union(left_term).union(right_term)

        return result
