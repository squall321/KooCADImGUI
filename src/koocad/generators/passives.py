"""
Passive component generators (resistors, capacitors, crystals, etc.).

This module generates various passive electronic components.
"""

from __future__ import annotations

from typing import List

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class ChipResistorGenerator(ComponentGenerator):
    """Generator for chip (SMD) resistors."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate chip resistor parameters.

        Required parameters:
        - body_length: Resistor length (mm)
        - body_width: Resistor width (mm)
        - body_height: Resistor height (mm)
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
        """Generate chip resistor shape.

        Structure:
        1. Ceramic body
        2. Resistive element on top (laser trim pattern)
        3. End terminations
        """
        params = context.parameters.evaluate_all()

        length = params["body_length"]
        width = params["body_width"]
        height = params["body_height"]
        term_length = params["termination_length"]

        # Create resistor body (ceramic substrate)
        body = self.kernel.box(
            width=length - 2 * term_length,
            height=width,
            depth=height,
            centered=True,
        )

        # Create resistive element on top (simplified as thin box)
        element_thickness = height * 0.05
        element = self.kernel.box(
            width=length * 0.8,
            height=width * 0.6,
            depth=element_thickness,
            centered=True,
        )
        element = element.translate(0, 0, height / 2 + element_thickness / 2)

        # Create left termination
        left_term = self.kernel.box(
            width=term_length,
            height=width,
            depth=height,
            centered=False,
        )
        left_term = left_term.translate(-length / 2, -width / 2, -height / 2)

        # Create right termination
        right_term = self.kernel.box(
            width=term_length,
            height=width,
            depth=height,
            centered=False,
        )
        right_term = right_term.translate(length / 2 - term_length, -width / 2, -height / 2)

        # Combine all parts
        result = body.union(element).union(left_term).union(right_term)

        return result


class CrystalOscillatorGenerator(ComponentGenerator):
    """Generator for crystal oscillator packages."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate crystal oscillator parameters.

        Required parameters:
        - package_length: Package length (mm)
        - package_width: Package width (mm)
        - package_height: Package height (mm)
        - crystal_type: "smd" or "through_hole"
        """
        errors = []

        required = [
            "package_length",
            "package_width",
            "package_height",
            "crystal_type",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            if values["crystal_type"] not in ["smd", "through_hole"]:
                errors.append("Crystal type must be 'smd' or 'through_hole'")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate crystal oscillator shape."""
        params = context.parameters.evaluate_all()

        length = params["package_length"]
        width = params["package_width"]
        height = params["package_height"]
        crystal_type = params["crystal_type"]

        # Create metal can housing
        housing = self.kernel.box(
            width=length,
            height=width,
            depth=height,
            centered=True,
        )

        # Add chamfer to top edges for realistic appearance
        try:
            chamfer_radius = min(length, width) * 0.1
            housing = housing.fillet(chamfer_radius)
        except Exception:
            pass  # Fillet might fail

        result = housing

        if crystal_type == "through_hole":
            # Add pins for through-hole type
            pin_dia = 0.5
            pin_length = 3.0

            # Create 4 pins at corners
            pin_offset = min(length, width) * 0.3

            for x in [-1, 1]:
                for y in [-1, 1]:
                    pin = self.kernel.cylinder(
                        radius=pin_dia / 2,
                        height=pin_length,
                        centered=False,
                    )
                    pin = pin.translate(
                        x * pin_offset,
                        y * pin_offset,
                        -height / 2 - pin_length,
                    )
                    result = result.union(pin)

        else:  # SMD type
            # Add pads on bottom
            pad_length = length * 0.2
            pad_width = width * 0.3
            pad_thickness = height * 0.05

            for x in [-1, 1]:
                pad = self.kernel.box(
                    width=pad_length,
                    height=pad_width,
                    depth=pad_thickness,
                    centered=True,
                )
                pad = pad.translate(
                    x * length * 0.35,
                    0,
                    -height / 2 - pad_thickness / 2,
                )
                result = result.union(pad)

        return result


class TantalumCapacitorGenerator(ComponentGenerator):
    """Generator for tantalum electrolytic capacitors."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate tantalum capacitor parameters.

        Required parameters:
        - body_length: Body length (mm)
        - body_width: Body width (mm)
        - body_height: Body height (mm)
        - cathode_length: Cathode termination length (mm)
        - anode_length: Anode termination length (mm)
        """
        errors = []

        required = [
            "body_length",
            "body_width",
            "body_height",
            "cathode_length",
            "anode_length",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate tantalum capacitor shape.

        Tantalum caps have a rectangular body with beveled edges
        and polarity-marked terminations.
        """
        params = context.parameters.evaluate_all()

        length = params["body_length"]
        width = params["body_width"]
        height = params["body_height"]
        cathode_length = params["cathode_length"]
        anode_length = params["anode_length"]

        # Create main body
        body = self.kernel.box(
            width=length - cathode_length - anode_length,
            height=width,
            depth=height,
            centered=True,
        )

        # Add polarity mark (stripe on cathode end)
        stripe_width = width
        stripe_height = height * 0.8
        stripe_thickness = 0.1

        stripe = self.kernel.box(
            width=stripe_thickness,
            height=stripe_width,
            depth=stripe_height,
            centered=True,
        )
        stripe = stripe.translate(-length / 2 + cathode_length + 0.5, 0, 0)
        body = body.union(stripe)

        # Create cathode termination (marked end)
        cathode = self.kernel.box(
            width=cathode_length,
            height=width,
            depth=height * 0.7,
            centered=False,
        )
        cathode = cathode.translate(
            -length / 2,
            -width / 2,
            -height * 0.35,
        )

        # Create anode termination
        anode = self.kernel.box(
            width=anode_length,
            height=width,
            depth=height * 0.7,
            centered=False,
        )
        anode = anode.translate(
            length / 2 - anode_length,
            -width / 2,
            -height * 0.35,
        )

        # Combine all parts
        result = body.union(cathode).union(anode)

        return result


class LEDGenerator(ComponentGenerator):
    """Generator for LED packages (through-hole and SMD)."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate LED parameters.

        Required parameters:
        - led_type: "through_hole" or "smd"
        - body_diameter: LED body diameter (mm) for through-hole
        - body_length: Body length (mm) for SMD
        - body_width: Body width (mm) for SMD
        - body_height: Body height (mm)
        """
        errors = []

        required = ["led_type", "body_height"]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            led_type = values["led_type"]

            if led_type not in ["through_hole", "smd"]:
                errors.append("LED type must be 'through_hole' or 'smd'")

            if led_type == "through_hole" and "body_diameter" not in params.parameters:
                errors.append("through_hole LED requires body_diameter")

            if led_type == "smd":
                if "body_length" not in params.parameters:
                    errors.append("SMD LED requires body_length")
                if "body_width" not in params.parameters:
                    errors.append("SMD LED requires body_width")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate LED shape."""
        params = context.parameters.evaluate_all()

        led_type = params["led_type"]
        height = params["body_height"]

        if led_type == "through_hole":
            # Create cylindrical LED body
            diameter = params["body_diameter"]

            body = self.kernel.cylinder(
                radius=diameter / 2,
                height=height,
                centered=True,
            )

            # Add dome on top
            dome = self.kernel.sphere(
                radius=diameter / 2,
                center=(0, 0, height / 2),
            )

            # Trim bottom of dome
            trim = self.kernel.box(
                width=diameter * 2,
                height=diameter * 2,
                depth=height,
                centered=True,
            )
            trim = trim.translate(0, 0, height / 4)
            dome = dome.intersect(trim)

            body = body.union(dome)

            # Add leads
            lead_dia = 0.5
            lead_length = 10.0
            lead_spacing = 2.54

            for x in [-lead_spacing / 2, lead_spacing / 2]:
                lead = self.kernel.cylinder(
                    radius=lead_dia / 2,
                    height=lead_length,
                    centered=False,
                )
                lead = lead.translate(x, 0, -height / 2 - lead_length)
                body = body.union(lead)

            result = body

        else:  # SMD LED
            length = params["body_length"]
            width = params["body_width"]

            # Create rectangular SMD LED body
            body = self.kernel.box(
                width=length,
                height=width,
                depth=height,
                centered=True,
            )

            # Add cathode mark
            mark_width = length * 0.2
            mark = self.kernel.box(
                width=mark_width,
                height=width,
                depth=height * 0.1,
                centered=True,
            )
            mark = mark.translate(-length / 2 + mark_width / 2, 0, height / 2 + height * 0.05)
            body = body.union(mark)

            # Add end terminations
            term_length = length * 0.15
            term_height = height * 0.5

            for x in [-1, 1]:
                term = self.kernel.box(
                    width=term_length,
                    height=width,
                    depth=term_height,
                    centered=False,
                )
                if x < 0:
                    term = term.translate(-length / 2, -width / 2, -height / 2)
                else:
                    term = term.translate(length / 2 - term_length, -width / 2, -height / 2)

                body = body.union(term)

            result = body

        return result


class FuseGenerator(ComponentGenerator):
    """Generator for fuse components."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate fuse parameters.

        Required parameters:
        - body_length: Fuse body length (mm)
        - body_diameter: Fuse body diameter (mm)
        - cap_length: End cap length (mm)
        """
        errors = []

        required = [
            "body_length",
            "body_diameter",
            "cap_length",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate fuse shape (cartridge style)."""
        params = context.parameters.evaluate_all()

        length = params["body_length"]
        diameter = params["body_diameter"]
        cap_length = params["cap_length"]

        # Create glass/ceramic body
        body = self.kernel.cylinder(
            radius=diameter / 2,
            height=length - 2 * cap_length,
            centered=True,
        )

        # Create metal end caps
        cap_radius = diameter / 2 * 1.05  # Slightly larger

        left_cap = self.kernel.cylinder(
            radius=cap_radius,
            height=cap_length,
            centered=False,
        )
        left_cap = left_cap.translate(0, 0, -length / 2)

        right_cap = self.kernel.cylinder(
            radius=cap_radius,
            height=cap_length,
            centered=False,
        )
        right_cap = right_cap.translate(0, 0, length / 2 - cap_length)

        # Combine all parts
        result = body.union(left_cap).union(right_cap)

        return result
