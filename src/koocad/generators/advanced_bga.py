"""
Advanced BGA and WLP (Wafer Level Package) generators.

This module provides sophisticated BGA/WLP features including multilayer
substrates, routing, wirebonding, and flip-chip bumping.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class BallPattern(Enum):
    """Ball array pattern types."""

    FULL = "full"
    PERIPHERAL = "peripheral"
    CUSTOM = "custom"


class SolderMaskType(Enum):
    """Solder mask opening types."""

    NSMD = "nsmd"  # Non-Solder Mask Defined
    SMD = "smd"  # Solder Mask Defined


@dataclass
class LayerStackup:
    """PCB layer stackup definition."""

    layer_name: str
    thickness: float  # mm
    material: str
    copper_weight: Optional[float] = None  # oz


@dataclass
class WirebondProfile:
    """Wirebond wire profile parameters."""

    wire_diameter: float  # mm
    loop_height: float  # mm
    bond_angle: float  # degrees
    wire_material: str = "Gold"


class MultilayerBGAGenerator(ComponentGenerator):
    """Generator for multilayer BGA with complex substrate."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate multilayer BGA parameters.

        Required parameters:
        - substrate_width, substrate_height, substrate_thickness
        - ball_rows, ball_cols, ball_pitch, ball_diameter
        - layer_count: Number of substrate layers
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
            "layer_count",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            if values["layer_count"] < 2:
                errors.append("Layer count must be at least 2")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate multilayer BGA with visible layer structure."""
        params = context.parameters.evaluate_all()

        substrate_width = params["substrate_width"]
        substrate_height = params["substrate_height"]
        substrate_thickness = params["substrate_thickness"]
        ball_rows = int(params["ball_rows"])
        ball_cols = int(params["ball_cols"])
        ball_pitch = params["ball_pitch"]
        ball_diameter = params["ball_diameter"]
        layer_count = int(params["layer_count"])

        # Create substrate with visible layers
        layer_thickness = substrate_thickness / layer_count

        substrate = None
        for i in range(layer_count):
            z_offset = -substrate_thickness / 2 + i * layer_thickness

            layer = self.kernel.box(
                width=substrate_width,
                height=substrate_height,
                depth=layer_thickness,
                centered=True,
            )
            layer = layer.translate(0, 0, z_offset + layer_thickness / 2)

            if substrate is None:
                substrate = layer
            else:
                substrate = substrate.union(layer)

        # Add ball array
        ball_radius = ball_diameter / 2
        array_width = (ball_cols - 1) * ball_pitch
        array_height = (ball_rows - 1) * ball_pitch
        x_offset = -array_width / 2
        y_offset = -array_height / 2
        z_offset = -substrate_thickness / 2 - ball_radius

        result = substrate

        for row in range(ball_rows):
            for col in range(ball_cols):
                x = x_offset + col * ball_pitch
                y = y_offset + row * ball_pitch
                z = z_offset

                ball = self.kernel.sphere(radius=ball_radius, center=(x, y, z))
                result = result.union(ball)

        return result


class FanOutBGAGenerator(ComponentGenerator):
    """Generator for BGA with fan-out routing pattern."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate fan-out BGA parameters."""
        errors = []

        required = [
            "substrate_width",
            "substrate_height",
            "substrate_thickness",
            "ball_pitch",
            "ball_diameter",
            "fanout_layers",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate BGA with fan-out routing traces (simplified)."""
        params = context.parameters.evaluate_all()

        substrate_width = params["substrate_width"]
        substrate_height = params["substrate_height"]
        substrate_thickness = params["substrate_thickness"]
        ball_pitch = params["ball_pitch"]
        ball_diameter = params["ball_diameter"]

        # Create substrate
        substrate = self.kernel.box(
            width=substrate_width,
            height=substrate_height,
            depth=substrate_thickness,
            centered=True,
        )

        # Add simplified routing traces on top layer
        # (In real design, these would be copper traces with specific impedance)
        trace_width = ball_pitch * 0.3
        trace_thickness = 0.035  # 1oz copper

        # Create radial fan-out pattern (simplified)
        num_traces = 8
        for i in range(num_traces):
            angle = (360 / num_traces) * i
            angle_rad = math.radians(angle)

            # Calculate trace endpoints
            start_r = substrate_width * 0.1
            end_r = substrate_width * 0.4

            start_x = start_r * math.cos(angle_rad)
            start_y = start_r * math.sin(angle_rad)
            end_x = end_r * math.cos(angle_rad)
            end_y = end_r * math.sin(angle_rad)

            # Create trace as thin box (simplified representation)
            trace_length = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
            trace = self.kernel.box(
                width=trace_length,
                height=trace_width,
                depth=trace_thickness,
                centered=True,
            )

            # Rotate and position trace
            trace = trace.rotate((0, 0, 1), angle)
            trace = trace.translate(
                (start_x + end_x) / 2,
                (start_y + end_y) / 2,
                substrate_thickness / 2 + trace_thickness / 2,
            )

            substrate = substrate.union(trace)

        # Add ball array (simplified - just corners)
        ball_radius = ball_diameter / 2
        ball_positions = [
            (-substrate_width * 0.3, -substrate_height * 0.3),
            (substrate_width * 0.3, -substrate_height * 0.3),
            (-substrate_width * 0.3, substrate_height * 0.3),
            (substrate_width * 0.3, substrate_height * 0.3),
        ]

        result = substrate

        for x, y in ball_positions:
            z = -substrate_thickness / 2 - ball_radius
            ball = self.kernel.sphere(radius=ball_radius, center=(x, y, z))
            result = result.union(ball)

        return result


class WirebondPackageGenerator(ComponentGenerator):
    """Generator for wire-bonded packages with visible wire loops."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate wirebond package parameters.

        Required parameters:
        - substrate_width, substrate_height, substrate_thickness
        - die_width, die_height, die_thickness
        - wire_diameter, loop_height
        - bond_pad_count
        """
        errors = []

        required = [
            "substrate_width",
            "substrate_height",
            "substrate_thickness",
            "die_width",
            "die_height",
            "die_thickness",
            "wire_diameter",
            "loop_height",
            "bond_pad_count",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate wirebond package with catenary wire profiles."""
        params = context.parameters.evaluate_all()

        substrate_width = params["substrate_width"]
        substrate_height = params["substrate_height"]
        substrate_thickness = params["substrate_thickness"]
        die_width = params["die_width"]
        die_height = params["die_height"]
        die_thickness = params["die_thickness"]
        wire_diameter = params["wire_diameter"]
        loop_height = params["loop_height"]
        bond_pad_count = int(params["bond_pad_count"])

        # Create substrate
        substrate = self.kernel.box(
            width=substrate_width,
            height=substrate_height,
            depth=substrate_thickness,
            centered=True,
        )

        # Create die (silicon chip)
        die = self.kernel.box(
            width=die_width,
            height=die_height,
            depth=die_thickness,
            centered=True,
        )
        die = die.translate(0, 0, substrate_thickness / 2 + die_thickness / 2)

        result = substrate.union(die)

        # Create simplified wirebond wires (as cylinders)
        # In reality, these would be catenary curves
        wire_radius = wire_diameter / 2

        # Place wires around die perimeter
        die_edge = die_width / 2
        substrate_edge = substrate_width / 2 - substrate_width * 0.1

        for i in range(bond_pad_count):
            # Distribute bonds around die
            angle = (360 / bond_pad_count) * i
            angle_rad = math.radians(angle)

            # Die pad position
            die_x = die_edge * 0.9 * math.cos(angle_rad)
            die_y = die_edge * 0.9 * math.sin(angle_rad)
            die_z = substrate_thickness / 2 + die_thickness

            # Substrate pad position
            sub_x = substrate_edge * math.cos(angle_rad)
            sub_y = substrate_edge * math.sin(angle_rad)
            sub_z = substrate_thickness / 2

            # Create wire as cylinder (simplified - should be curve)
            wire_length = math.sqrt((sub_x - die_x) ** 2 + (sub_y - die_y) ** 2 + (sub_z - die_z) ** 2)

            wire = self.kernel.cylinder(
                radius=wire_radius,
                height=wire_length,
                centered=True,
            )

            # Calculate rotation angles
            dx = sub_x - die_x
            dy = sub_y - die_y
            dz = sub_z - die_z

            # Rotate wire to connect die to substrate
            angle_xy = math.degrees(math.atan2(dy, dx))
            angle_z = math.degrees(math.atan2(dz, math.sqrt(dx * dx + dy * dy)))

            wire = wire.rotate((0, 0, 1), angle_xy)
            wire = wire.rotate((0, 1, 0), -angle_z)
            wire = wire.translate((die_x + sub_x) / 2, (die_y + sub_y) / 2, (die_z + sub_z) / 2)

            result = result.union(wire)

        return result


class FlipChipBumpGenerator(ComponentGenerator):
    """Generator for flip-chip packages with C4 bumps or copper pillars."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate flip-chip parameters.

        Required parameters:
        - substrate_width, substrate_height, substrate_thickness
        - die_width, die_height, die_thickness
        - bump_pitch, bump_diameter, bump_height
        - bump_type: "c4" or "copper_pillar"
        """
        errors = []

        required = [
            "substrate_width",
            "substrate_height",
            "substrate_thickness",
            "die_width",
            "die_height",
            "die_thickness",
            "bump_pitch",
            "bump_diameter",
            "bump_height",
            "bump_type",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            if values["bump_type"] not in ["c4", "copper_pillar", "micro_bump"]:
                errors.append("Bump type must be 'c4', 'copper_pillar', or 'micro_bump'")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate flip-chip package with bumps."""
        params = context.parameters.evaluate_all()

        substrate_width = params["substrate_width"]
        substrate_height = params["substrate_height"]
        substrate_thickness = params["substrate_thickness"]
        die_width = params["die_width"]
        die_height = params["die_height"]
        die_thickness = params["die_thickness"]
        bump_pitch = params["bump_pitch"]
        bump_diameter = params["bump_diameter"]
        bump_height = params["bump_height"]
        bump_type = params["bump_type"]

        # Create substrate
        substrate = self.kernel.box(
            width=substrate_width,
            height=substrate_height,
            depth=substrate_thickness,
            centered=True,
        )

        # Calculate bump array
        bump_cols = int(die_width / bump_pitch)
        bump_rows = int(die_height / bump_pitch)

        array_width = (bump_cols - 1) * bump_pitch
        array_height = (bump_rows - 1) * bump_pitch
        x_offset = -array_width / 2
        y_offset = -array_height / 2

        result = substrate

        # Create bumps
        for row in range(bump_rows):
            for col in range(bump_cols):
                x = x_offset + col * bump_pitch
                y = y_offset + row * bump_pitch
                z = substrate_thickness / 2

                if bump_type == "c4":
                    # C4 bump (solder ball)
                    bump = self.kernel.sphere(radius=bump_diameter / 2, center=(x, y, z + bump_height / 2))
                elif bump_type == "copper_pillar":
                    # Copper pillar (cylinder)
                    bump = self.kernel.cylinder(
                        radius=bump_diameter / 2,
                        height=bump_height,
                        centered=False,
                    )
                    bump = bump.translate(x, y, z)
                else:  # micro_bump
                    # Micro bump (small sphere for TSV)
                    bump = self.kernel.sphere(radius=bump_diameter / 2, center=(x, y, z + bump_height / 2))

                result = result.union(bump)

        # Add die on top of bumps (flipped)
        die = self.kernel.box(
            width=die_width,
            height=die_height,
            depth=die_thickness,
            centered=True,
        )
        die = die.translate(0, 0, substrate_thickness / 2 + bump_height + die_thickness / 2)

        result = result.union(die)

        return result


class WLPGenerator(ComponentGenerator):
    """Generator for Wafer Level Packages with RDL (Redistribution Layer)."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate WLP parameters.

        Required parameters:
        - die_width, die_height, die_thickness
        - bump_pitch, bump_diameter
        - rdl_layers: Number of redistribution layers
        """
        errors = []

        required = [
            "die_width",
            "die_height",
            "die_thickness",
            "bump_pitch",
            "bump_diameter",
            "rdl_layers",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate WLP with RDL and bumps."""
        params = context.parameters.evaluate_all()

        die_width = params["die_width"]
        die_height = params["die_height"]
        die_thickness = params["die_thickness"]
        bump_pitch = params["bump_pitch"]
        bump_diameter = params["bump_diameter"]
        rdl_layers = int(params["rdl_layers"])

        # Create silicon die
        die = self.kernel.box(
            width=die_width,
            height=die_height,
            depth=die_thickness,
            centered=True,
        )

        result = die

        # Add RDL layers on top
        rdl_thickness = 0.01  # 10 microns per layer
        for i in range(rdl_layers):
            z_offset = die_thickness / 2 + i * rdl_thickness

            rdl = self.kernel.box(
                width=die_width,
                height=die_height,
                depth=rdl_thickness,
                centered=True,
            )
            rdl = rdl.translate(0, 0, z_offset + rdl_thickness / 2)

            result = result.union(rdl)

        # Add solder bumps on top
        bump_cols = int(die_width / bump_pitch)
        bump_rows = int(die_height / bump_pitch)

        array_width = (bump_cols - 1) * bump_pitch
        array_height = (bump_rows - 1) * bump_pitch
        x_offset = -array_width / 2
        y_offset = -array_height / 2
        z_base = die_thickness / 2 + rdl_layers * rdl_thickness

        for row in range(bump_rows):
            for col in range(bump_cols):
                x = x_offset + col * bump_pitch
                y = y_offset + row * bump_pitch

                bump = self.kernel.sphere(radius=bump_diameter / 2, center=(x, y, z_base + bump_diameter / 2))
                result = result.union(bump)

        return result
