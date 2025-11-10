"""
Connector component generators.

This module generates various connector types including pin headers,
board-to-board connectors, and USB connectors.
"""

from __future__ import annotations

from typing import List

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class PinHeaderGenerator(ComponentGenerator):
    """Generator for pin header connectors.

    Pin headers are through-hole connectors with rows of pins.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate pin header parameters.

        Required parameters:
        - pin_count: Number of pins
        - pin_rows: Number of rows (1 or 2)
        - pin_pitch: Pitch between pins (mm)
        - pin_diameter: Pin diameter (mm)
        - pin_length: Pin length (mm)
        - housing_height: Plastic housing height (mm)
        """
        errors = []

        required = [
            "pin_count",
            "pin_rows",
            "pin_pitch",
            "pin_diameter",
            "pin_length",
            "housing_height",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            if values["pin_rows"] not in [1, 2]:
                errors.append("Pin rows must be 1 or 2")

            if values["pin_count"] < 1:
                errors.append("Pin count must be at least 1")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate pin header shape.

        Structure:
        1. Plastic housing (rectangular body)
        2. Metal pins (cylinders)
        """
        params = context.parameters.evaluate_all()

        pin_count = int(params["pin_count"])
        pin_rows = int(params["pin_rows"])
        pitch = params["pin_pitch"]
        pin_dia = params["pin_diameter"]
        pin_len = params["pin_length"]
        housing_height = params["housing_height"]

        # Calculate housing dimensions
        pins_per_row = pin_count // pin_rows
        housing_length = (pins_per_row - 1) * pitch + pitch
        housing_width = pitch if pin_rows == 1 else pitch * 2

        # Create plastic housing
        housing = self.kernel.box(
            width=housing_length,
            height=housing_width,
            depth=housing_height,
            centered=True,
        )

        # Create pins
        result = housing

        for row in range(pin_rows):
            for col in range(pins_per_row):
                # Calculate pin position
                x = -housing_length / 2 + pitch / 2 + col * pitch
                y = -pitch / 2 if pin_rows == 2 and row == 0 else pitch / 2 if pin_rows == 2 else 0
                z = -housing_height / 2 - pin_len / 2

                # Create pin
                pin = self.kernel.cylinder(
                    radius=pin_dia / 2,
                    height=pin_len + housing_height / 2,
                    centered=True,
                )
                pin = pin.translate(x, y, z)

                # Add to result
                result = result.union(pin)

        return result


class BoardToBoardConnectorGenerator(ComponentGenerator):
    """Generator for board-to-board mezzanine connectors."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate board-to-board connector parameters.

        Required parameters:
        - contact_count: Number of contacts
        - contact_pitch: Pitch between contacts (mm)
        - housing_height: Connector height (mm)
        - housing_width: Connector width (mm)
        """
        errors = []

        required = [
            "contact_count",
            "contact_pitch",
            "housing_height",
            "housing_width",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate board-to-board connector shape."""
        params = context.parameters.evaluate_all()

        contact_count = int(params["contact_count"])
        pitch = params["contact_pitch"]
        height = params["housing_height"]
        width = params["housing_width"]

        # Calculate housing length based on contacts
        housing_length = (contact_count - 1) * pitch + pitch * 2

        # Create main housing
        housing = self.kernel.box(
            width=housing_length,
            height=width,
            depth=height,
            centered=True,
        )

        # Create simplified contact pattern (array of small boxes)
        contact_width = pitch * 0.3
        contact_height = pitch * 0.3
        contact_depth = height * 0.8

        result = housing

        for i in range(contact_count):
            x = -housing_length / 2 + pitch + i * pitch
            y = 0
            z = 0

            contact = self.kernel.box(
                width=contact_width,
                height=contact_height,
                depth=contact_depth,
                centered=True,
            )
            contact = contact.translate(x, y, z)

            result = result.union(contact)

        return result


class USBConnectorGenerator(ComponentGenerator):
    """Generator for USB connector models.

    Simplified USB Type-A or Type-C connector housing.
    """

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate USB connector parameters.

        Required parameters:
        - connector_type: "type_a" or "type_c"
        - housing_length: Length (mm)
        - housing_width: Width (mm)
        - housing_height: Height (mm)
        """
        errors = []

        required = [
            "connector_type",
            "housing_length",
            "housing_width",
            "housing_height",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            if values["connector_type"] not in ["type_a", "type_c"]:
                errors.append("Connector type must be 'type_a' or 'type_c'")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate USB connector shape."""
        params = context.parameters.evaluate_all()

        conn_type = params["connector_type"]
        length = params["housing_length"]
        width = params["housing_width"]
        height = params["housing_height"]

        # Create outer housing
        housing = self.kernel.box(
            width=length,
            height=width,
            depth=height,
            centered=True,
        )

        # Create internal cavity (receptacle)
        cavity_length = length * 0.7
        cavity_width = width * 0.4 if conn_type == "type_a" else width * 0.7
        cavity_height = height * 0.3 if conn_type == "type_a" else height * 0.4

        cavity = self.kernel.box(
            width=cavity_length,
            height=cavity_width,
            depth=cavity_height,
            centered=True,
        )

        # Position cavity
        cavity = cavity.translate(length * 0.1, 0, 0)

        # Subtract cavity from housing
        result = housing.subtract(cavity)

        # Add mounting tabs (simplified as small boxes)
        tab_width = width * 0.3
        tab_height = height * 0.2
        tab_depth = height * 0.1

        tab1 = self.kernel.box(
            width=tab_width,
            height=tab_height,
            depth=tab_depth,
            centered=True,
        )
        tab1 = tab1.translate(-length / 2 - tab_width / 2, 0, height / 2 - tab_depth / 2)

        tab2 = self.kernel.box(
            width=tab_width,
            height=tab_height,
            depth=tab_depth,
            centered=True,
        )
        tab2 = tab2.translate(-length / 2 - tab_width / 2, 0, -height / 2 + tab_depth / 2)

        result = result.union(tab1).union(tab2)

        return result


class RJ45ConnectorGenerator(ComponentGenerator):
    """Generator for RJ45 Ethernet connector."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate RJ45 parameters.

        Required parameters:
        - housing_width: Width (mm)
        - housing_height: Height (mm)
        - housing_depth: Depth (mm)
        """
        errors = []

        required = [
            "housing_width",
            "housing_height",
            "housing_depth",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate RJ45 connector shape."""
        params = context.parameters.evaluate_all()

        width = params["housing_width"]
        height = params["housing_height"]
        depth = params["housing_depth"]

        # Create main housing (tall rectangular box)
        housing = self.kernel.box(
            width=width,
            height=depth,
            depth=height,
            centered=True,
        )

        # Create jack opening (rectangular cavity)
        jack_width = width * 0.7
        jack_depth = depth * 0.6
        jack_height = height * 0.4

        jack = self.kernel.box(
            width=jack_width,
            height=jack_depth,
            depth=jack_height,
            centered=True,
        )
        jack = jack.translate(0, depth * 0.2, height * 0.2)

        # Subtract jack opening
        result = housing.subtract(jack)

        # Add mounting pegs (simplified)
        peg_radius = width * 0.08
        peg_height = height * 0.3

        peg = self.kernel.cylinder(
            radius=peg_radius,
            height=peg_height,
            centered=True,
        )

        peg1 = peg.translate(-width * 0.3, -depth / 2 - peg_height / 2, -height / 2)
        peg2 = peg.translate(width * 0.3, -depth / 2 - peg_height / 2, -height / 2)

        result = result.union(peg1).union(peg2)

        return result
