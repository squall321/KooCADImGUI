"""
IC package generators for various package types.

This module generates standard IC packages including DIP, SOIC, QFP, QFN, etc.
"""

from __future__ import annotations

import math
from typing import List

from koocad.core.parameters import ParameterSet
from koocad.generators.base import ComponentGenerator, GenerationContext
from koocad.kernels.base import Shape


class DIPGenerator(ComponentGenerator):
    """Generator for DIP (Dual Inline Package) through-hole packages."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate DIP parameters.

        Required parameters:
        - pin_count: Total number of pins (must be even)
        - pin_pitch: Pitch between pins (typically 2.54mm)
        - body_width: Package body width (mm)
        - body_length: Package body length (mm)
        - body_height: Package body height (mm)
        - pin_width: Pin width (mm)
        - pin_length: Pin length extending from body (mm)
        """
        errors = []

        required = [
            "pin_count",
            "pin_pitch",
            "body_width",
            "body_length",
            "body_height",
            "pin_width",
            "pin_length",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            pin_count = int(values["pin_count"])

            if pin_count < 2:
                errors.append("Pin count must be at least 2")

            if pin_count % 2 != 0:
                errors.append("Pin count must be even")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate DIP package shape."""
        params = context.parameters.evaluate_all()

        pin_count = int(params["pin_count"])
        pitch = params["pin_pitch"]
        body_width = params["body_width"]
        body_length = params["body_length"]
        body_height = params["body_height"]
        pin_width = params["pin_width"]
        pin_length = params["pin_length"]

        pins_per_side = pin_count // 2

        # Create package body
        body = self.kernel.box(
            width=body_length,
            height=body_width,
            depth=body_height,
            centered=True,
        )

        # Add notch at one end for orientation
        notch_width = body_width * 0.2
        notch_depth = body_height * 0.2
        notch = self.kernel.cylinder(
            radius=notch_width / 2,
            height=notch_depth,
            centered=True,
        )
        notch = notch.rotate((1, 0, 0), 90)
        notch = notch.translate(0, 0, body_height / 2)
        body = body.subtract(notch)

        result = body

        # Create pins on both sides
        pin_thickness = body_height * 0.1

        for i in range(pins_per_side):
            # Calculate pin position
            pin_y = -(pins_per_side - 1) * pitch / 2 + i * pitch

            # Left side pins
            left_pin = self.kernel.box(
                width=pin_width,
                height=pin_length + body_width / 2,
                depth=pin_thickness,
                centered=False,
            )
            left_pin = left_pin.translate(
                -pin_width / 2,
                -body_width / 2 - pin_length,
                -body_height / 2,
            )
            left_pin = left_pin.translate(0, pin_y, 0)
            result = result.union(left_pin)

            # Right side pins
            right_pin = self.kernel.box(
                width=pin_width,
                height=pin_length + body_width / 2,
                depth=pin_thickness,
                centered=False,
            )
            right_pin = right_pin.translate(
                -pin_width / 2,
                body_width / 2,
                -body_height / 2,
            )
            right_pin = right_pin.translate(0, pin_y, 0)
            result = result.union(right_pin)

        return result


class SOICGenerator(ComponentGenerator):
    """Generator for SOIC (Small Outline IC) surface-mount packages."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate SOIC parameters.

        Required parameters:
        - pin_count: Total number of pins (must be even)
        - pin_pitch: Pitch between pins (typically 1.27mm)
        - body_width: Package body width (mm)
        - body_length: Package body length (mm)
        - body_height: Package body height (mm)
        - lead_width: Lead width (mm)
        - lead_length: Lead length extending from body (mm)
        - lead_span: Distance between lead tips (mm)
        """
        errors = []

        required = [
            "pin_count",
            "pin_pitch",
            "body_width",
            "body_length",
            "body_height",
            "lead_width",
            "lead_length",
            "lead_span",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            pin_count = int(values["pin_count"])

            if pin_count % 2 != 0:
                errors.append("Pin count must be even")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate SOIC package with gull-wing leads."""
        params = context.parameters.evaluate_all()

        pin_count = int(params["pin_count"])
        pitch = params["pin_pitch"]
        body_width = params["body_width"]
        body_length = params["body_length"]
        body_height = params["body_height"]
        lead_width = params["lead_width"]
        lead_length = params["lead_length"]
        lead_span = params["lead_span"]

        pins_per_side = pin_count // 2

        # Create package body
        body = self.kernel.box(
            width=body_length,
            height=body_width,
            depth=body_height,
            centered=True,
        )

        result = body

        # Lead thickness
        lead_thickness = body_height * 0.15

        # Create gull-wing leads on both sides
        for i in range(pins_per_side):
            pin_y = -(pins_per_side - 1) * pitch / 2 + i * pitch

            # Left side lead
            left_lead = self.kernel.box(
                width=lead_width,
                height=lead_length,
                depth=lead_thickness,
                centered=False,
            )
            left_lead = left_lead.translate(
                -lead_width / 2,
                -lead_span / 2,
                -body_height / 2,
            )
            left_lead = left_lead.translate(0, pin_y, 0)
            result = result.union(left_lead)

            # Right side lead
            right_lead = self.kernel.box(
                width=lead_width,
                height=lead_length,
                depth=lead_thickness,
                centered=False,
            )
            right_lead = right_lead.translate(
                -lead_width / 2,
                lead_span / 2 - lead_length,
                -body_height / 2,
            )
            right_lead = right_lead.translate(0, pin_y, 0)
            result = result.union(right_lead)

        return result


class QFPGenerator(ComponentGenerator):
    """Generator for QFP/LQFP (Quad Flat Package) with leads on all 4 sides."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate QFP parameters.

        Required parameters:
        - pin_count: Total number of pins (must be divisible by 4)
        - pin_pitch: Pitch between pins (mm)
        - body_size: Package body size (square, mm)
        - body_height: Package body height (mm)
        - lead_width: Lead width (mm)
        - lead_length: Lead length extending from body (mm)
        - lead_span: Distance between lead tips (mm)
        """
        errors = []

        required = [
            "pin_count",
            "pin_pitch",
            "body_size",
            "body_height",
            "lead_width",
            "lead_length",
            "lead_span",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            pin_count = int(values["pin_count"])

            if pin_count < 4:
                errors.append("Pin count must be at least 4")

            if pin_count % 4 != 0:
                errors.append("Pin count must be divisible by 4 for QFP")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate QFP package with leads on 4 sides."""
        params = context.parameters.evaluate_all()

        pin_count = int(params["pin_count"])
        pitch = params["pin_pitch"]
        body_size = params["body_size"]
        body_height = params["body_height"]
        lead_width = params["lead_width"]
        lead_length = params["lead_length"]
        lead_span = params["lead_span"]

        pins_per_side = pin_count // 4

        # Create square package body
        body = self.kernel.box(
            width=body_size,
            height=body_size,
            depth=body_height,
            centered=True,
        )

        # Add corner chamfer for pin 1 indicator
        chamfer_size = body_size * 0.15
        chamfer = self.kernel.box(
            width=chamfer_size,
            height=chamfer_size,
            depth=body_height * 1.1,
            centered=True,
        )
        chamfer = chamfer.translate(-body_size / 2 + chamfer_size / 2, -body_size / 2 + chamfer_size / 2, 0)
        body = body.subtract(chamfer)

        result = body

        lead_thickness = body_height * 0.15

        # Create leads on all 4 sides
        for side in range(4):
            for i in range(pins_per_side):
                pos = -(pins_per_side - 1) * pitch / 2 + i * pitch

                # Create lead
                lead = self.kernel.box(
                    width=lead_width,
                    height=lead_length,
                    depth=lead_thickness,
                    centered=False,
                )

                # Position based on side
                if side == 0:  # Bottom
                    lead = lead.translate(-lead_width / 2, -lead_span / 2, -body_height / 2)
                    lead = lead.translate(pos, 0, 0)
                elif side == 1:  # Right
                    lead = lead.rotate((0, 0, 1), 90)
                    lead = lead.translate(lead_span / 2 - lead_length, pos, -body_height / 2)
                elif side == 2:  # Top
                    lead = lead.rotate((0, 0, 1), 180)
                    lead = lead.translate(pos, lead_span / 2 - lead_length, -body_height / 2)
                else:  # Left
                    lead = lead.rotate((0, 0, 1), 270)
                    lead = lead.translate(-lead_span / 2, pos, -body_height / 2)

                result = result.union(lead)

        return result


class QFNGenerator(ComponentGenerator):
    """Generator for QFN/DFN (Quad Flat No-lead) packages with exposed pad."""

    def validate_parameters(self, params: ParameterSet) -> List[str]:
        """Validate QFN parameters.

        Required parameters:
        - pin_count: Total number of pins
        - pin_pitch: Pitch between pins (mm)
        - body_size: Package body size (mm)
        - body_height: Package body height (mm)
        - pad_width: Pad width (mm)
        - pad_length: Pad length (mm)
        - exposed_pad_size: Central exposed pad size (mm)
        """
        errors = []

        required = [
            "pin_count",
            "pin_pitch",
            "body_size",
            "body_height",
            "pad_width",
            "pad_length",
            "exposed_pad_size",
        ]

        for param_name in required:
            if param_name not in params.parameters:
                errors.append(f"Missing required parameter: {param_name}")

        if not errors:
            values = params.evaluate_all()
            pin_count = int(values["pin_count"])

            if pin_count % 4 != 0:
                errors.append("Pin count must be divisible by 4")

        return errors

    def generate_shape(self, context: GenerationContext) -> Shape:
        """Generate QFN package with no leads (pads on bottom)."""
        params = context.parameters.evaluate_all()

        pin_count = int(params["pin_count"])
        pitch = params["pin_pitch"]
        body_size = params["body_size"]
        body_height = params["body_height"]
        pad_width = params["pad_width"]
        pad_length = params["pad_length"]
        exposed_pad_size = params["exposed_pad_size"]

        pins_per_side = pin_count // 4

        # Create square package body
        body = self.kernel.box(
            width=body_size,
            height=body_size,
            depth=body_height,
            centered=True,
        )

        result = body

        # Create exposed thermal pad at bottom center
        exposed_pad = self.kernel.box(
            width=exposed_pad_size,
            height=exposed_pad_size,
            depth=body_height * 0.1,
            centered=True,
        )
        exposed_pad = exposed_pad.translate(0, 0, -body_height / 2 - body_height * 0.05)
        result = result.union(exposed_pad)

        # Create edge pads on all 4 sides (simplified as small boxes)
        pad_thickness = body_height * 0.1

        for side in range(4):
            for i in range(pins_per_side):
                pos = -(pins_per_side - 1) * pitch / 2 + i * pitch

                pad = self.kernel.box(
                    width=pad_width,
                    height=pad_length,
                    depth=pad_thickness,
                    centered=False,
                )

                # Position on bottom edge
                if side == 0:  # Bottom
                    pad = pad.translate(-pad_width / 2, -body_size / 2, -body_height / 2 - pad_thickness)
                    pad = pad.translate(pos, 0, 0)
                elif side == 1:  # Right
                    pad = pad.rotate((0, 0, 1), 90)
                    pad = pad.translate(body_size / 2, pos, -body_height / 2 - pad_thickness)
                elif side == 2:  # Top
                    pad = pad.rotate((0, 0, 1), 180)
                    pad = pad.translate(pos, body_size / 2, -body_height / 2 - pad_thickness)
                else:  # Left
                    pad = pad.rotate((0, 0, 1), 270)
                    pad = pad.translate(-body_size / 2, pos, -body_height / 2 - pad_thickness)

                result = result.union(pad)

        return result
