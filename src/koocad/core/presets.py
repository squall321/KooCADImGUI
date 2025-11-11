"""
Parameter presets for standard electronic components.

This module provides predefined parameter sets following industry standards
like JEDEC, IPC, EIA, etc.
"""

from koocad.core.parameters import (
    EnumParameter,
    FloatParameter,
    IntParameter,
    ParameterSet,
    Unit,
)


class PresetLibrary:
    """Library of parameter presets."""

    def __init__(self) -> None:
        """Initialize preset library."""
        self.presets: dict[str, ParameterSet] = {}
        self._load_standard_presets()

    def _load_standard_presets(self) -> None:
        """Load standard industry presets."""
        # BGA presets (JEDEC standards)
        self.presets.update(BGAPresets.get_all())

        # MLCC presets (EIA standards)
        self.presets.update(MLCCPresets.get_all())

        # Resistor presets (EIA)
        self.presets.update(ResistorPresets.get_all())

    def get(self, name: str) -> ParameterSet | None:
        """Get preset by name.

        Args:
            name: Preset name.

        Returns:
            ParameterSet if found, None otherwise.

        Example:
            >>> library = PresetLibrary()
            >>> preset = library.get("BGA_15x15_0.8mm")
            >>> preset.get("ball_pitch").value
            0.8
        """
        return self.presets.get(name)

    def list_presets(self, category: str | None = None) -> list[str]:
        """List available preset names.

        Args:
            category: Filter by category (e.g., "BGA", "MLCC").

        Returns:
            List of preset names.
        """
        if category:
            return [name for name in self.presets.keys() if name.startswith(category)]
        return list(self.presets.keys())

    def add_preset(self, name: str, params: ParameterSet) -> None:
        """Add a custom preset.

        Args:
            name: Preset name.
            params: Parameter set.
        """
        self.presets[name] = params


class BGAPresets:
    """BGA package presets following JEDEC standards."""

    @staticmethod
    def get_all() -> dict[str, ParameterSet]:
        """Get all BGA presets."""
        return {
            "BGA_10x10_0.5mm": BGAPresets.create_standard(10, 10, 0.5),
            "BGA_12x12_0.5mm": BGAPresets.create_standard(12, 12, 0.5),
            "BGA_15x15_0.8mm": BGAPresets.create_standard(15, 15, 0.8),
            "BGA_17x17_1.0mm": BGAPresets.create_standard(17, 17, 1.0),
            "BGA_19x19_1.0mm": BGAPresets.create_standard(19, 19, 1.0),
            "BGA_23x23_1.0mm": BGAPresets.create_standard(23, 23, 1.0),
            "BGA_27x27_1.0mm": BGAPresets.create_standard(27, 27, 1.0),
        }

    @staticmethod
    def create_standard(
        rows: int,
        cols: int,
        pitch: float,
        *,
        substrate_thickness: float = 0.8,
    ) -> ParameterSet:
        """Create standard BGA preset.

        Args:
            rows: Number of ball rows.
            cols: Number of ball columns.
            pitch: Ball pitch in mm.
            substrate_thickness: Substrate thickness in mm.

        Returns:
            ParameterSet with BGA parameters.
        """
        params = ParameterSet()

        # Calculate substrate size
        substrate_size = (max(rows, cols) - 1) * pitch + 2.0  # 2mm margin

        params.add(
            FloatParameter(
                name="substrate_width",
                value=substrate_size,
                unit=Unit.MM,
            )
        )

        params.add(
            FloatParameter(
                name="substrate_height",
                value=substrate_size,
                unit=Unit.MM,
            )
        )

        params.add(
            FloatParameter(
                name="substrate_thickness",
                value=substrate_thickness,
                unit=Unit.MM,
            )
        )

        params.add(IntParameter(name="ball_rows", value=rows))
        params.add(IntParameter(name="ball_cols", value=cols))

        params.add(
            FloatParameter(
                name="ball_pitch",
                value=pitch,
                unit=Unit.MM,
            )
        )

        # Ball diameter (typically 60-75% of pitch)
        ball_diameter = pitch * 0.65
        params.add(
            FloatParameter(
                name="ball_diameter",
                value=ball_diameter,
                unit=Unit.MM,
            )
        )

        params.add(
            EnumParameter(
                name="ball_pattern",
                value="full",
                choices=["full", "peripheral", "custom"],
            )
        )

        params.add(IntParameter(name="layer_count", value=4))

        return params


class MLCCPresets:
    """MLCC (Multi-Layer Ceramic Capacitor) presets following EIA standards."""

    # EIA size codes: (length, width, height) in mm
    EIA_SIZES = {
        "0201": (0.6, 0.3, 0.3),
        "0402": (1.0, 0.5, 0.5),
        "0603": (1.6, 0.8, 0.8),
        "0805": (2.0, 1.25, 1.25),
        "1206": (3.2, 1.6, 1.6),
        "1210": (3.2, 2.5, 2.5),
        "1812": (4.5, 3.2, 2.5),
        "2220": (5.7, 5.0, 2.5),
    }

    @staticmethod
    def get_all() -> dict[str, ParameterSet]:
        """Get all MLCC presets."""
        presets = {}
        for size_code in MLCCPresets.EIA_SIZES:
            presets[f"MLCC_{size_code}"] = MLCCPresets.create_standard(size_code)
        return presets

    @staticmethod
    def create_standard(size_code: str) -> ParameterSet:
        """Create standard MLCC preset.

        Args:
            size_code: EIA size code (e.g., "0805").

        Returns:
            ParameterSet with MLCC parameters.
        """
        if size_code not in MLCCPresets.EIA_SIZES:
            raise ValueError(f"Unknown EIA size code: {size_code}")

        length, width, height = MLCCPresets.EIA_SIZES[size_code]

        params = ParameterSet()

        params.add(
            FloatParameter(
                name="body_length",
                value=length,
                unit=Unit.MM,
            )
        )

        params.add(
            FloatParameter(
                name="body_width",
                value=width,
                unit=Unit.MM,
            )
        )

        params.add(
            FloatParameter(
                name="body_height",
                value=height,
                unit=Unit.MM,
            )
        )

        # Termination (typically 20-30% of length)
        term_length = length * 0.25
        params.add(
            FloatParameter(
                name="termination_length",
                value=term_length,
                unit=Unit.MM,
            )
        )

        params.add(
            FloatParameter(
                name="termination_width",
                value=width * 0.9,
                unit=Unit.MM,
            )
        )

        # Layer count varies by size
        layer_count = {
            "0201": 50,
            "0402": 100,
            "0603": 200,
            "0805": 300,
            "1206": 400,
            "1210": 500,
            "1812": 600,
            "2220": 800,
        }.get(size_code, 200)

        params.add(IntParameter(name="layer_count", value=layer_count))

        params.add(
            FloatParameter(
                name="layer_thickness",
                value=2.0,  # µm
                unit=Unit.UM,
            )
        )

        return params


class ResistorPresets:
    """Chip resistor presets following EIA standards."""

    @staticmethod
    def get_all() -> dict[str, ParameterSet]:
        """Get all resistor presets."""
        presets = {}
        for size in ["0402", "0603", "0805", "1206", "1210", "2512"]:
            presets[f"RES_{size}"] = ResistorPresets.create_standard(size)
        return presets

    @staticmethod
    def create_standard(size_code: str) -> ParameterSet:
        """Create standard resistor preset."""
        # Use MLCC sizes as base
        length, width, height = MLCCPresets.EIA_SIZES.get(
            size_code,
            (2.0, 1.25, 0.5),
        )

        params = ParameterSet()

        params.add(FloatParameter(name="body_length", value=length, unit=Unit.MM))
        params.add(FloatParameter(name="body_width", value=width, unit=Unit.MM))
        params.add(FloatParameter(name="body_height", value=height * 0.6, unit=Unit.MM))

        params.add(
            FloatParameter(
                name="termination_length",
                value=length * 0.2,
                unit=Unit.MM,
            )
        )

        params.add(
            FloatParameter(
                name="resistor_thickness",
                value=0.02,  # mm
                unit=Unit.MM,
            )
        )

        return params


class PresetManager:
    """Manager for saving and loading custom presets."""

    @staticmethod
    def save_preset(name: str, params: ParameterSet, path: str) -> None:
        """Save preset to JSON file.

        Args:
            name: Preset name.
            params: Parameter set.
            path: File path.
        """
        import json
        from pathlib import Path

        data = {
            "name": name,
            "parameters": params.to_dict(),
        }

        Path(path).write_text(json.dumps(data, indent=2))

    @staticmethod
    def load_preset(path: str) -> ParameterSet:
        """Load preset from JSON file.

        Args:
            path: File path.

        Returns:
            ParameterSet.
        """
        import json
        from pathlib import Path

        data = json.loads(Path(path).read_text())
        return ParameterSet.from_dict(data["parameters"])
