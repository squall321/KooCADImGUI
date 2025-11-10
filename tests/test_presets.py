"""
Pytest test suite for KooCAD preset system.

Tests for industry-standard presets (JEDEC, EIA standards).
"""

import pytest
from koocad.core.presets import BGAPresets, MLCCPresets, ResistorPresets, PresetLibrary
from koocad.core.parameters import ParameterSet


class TestBGAPresets:
    """Test BGA preset functionality."""

    def test_get_all_bga_presets(self):
        """Test retrieving all BGA presets."""
        presets = BGAPresets.get_all()

        assert len(presets) == 7
        assert 'BGA_15x15_0.8mm' in presets
        assert 'BGA_10x10_0.5mm' in presets

    def test_bga_preset_structure(self):
        """Test BGA preset has correct structure."""
        preset = BGAPresets.get_all()['BGA_15x15_0.8mm']

        assert isinstance(preset, ParameterSet)
        assert 'ball_rows' in preset.parameters
        assert 'ball_cols' in preset.parameters
        assert 'ball_pitch' in preset.parameters
        assert 'substrate_width' in preset.parameters

    def test_bga_preset_values(self):
        """Test BGA preset has correct values."""
        preset = BGAPresets.get_all()['BGA_15x15_0.8mm']
        values = preset.evaluate_all()

        assert values['ball_rows'] == 15.0
        assert values['ball_cols'] == 15.0
        assert values['ball_pitch'] == 0.8
        assert values['substrate_thickness'] == 0.8

    def test_create_custom_bga(self):
        """Test creating custom BGA preset."""
        custom = BGAPresets.create_standard(
            rows=20,
            cols=20,
            pitch=0.5,
            substrate_thickness=1.0
        )

        values = custom.evaluate_all()

        assert values['ball_rows'] == 20.0
        assert values['ball_cols'] == 20.0
        assert values['ball_pitch'] == 0.5
        assert values['substrate_thickness'] == 1.0

    def test_ball_diameter_calculation(self):
        """Test ball diameter is calculated correctly (65% of pitch)."""
        preset = BGAPresets.get_all()['BGA_15x15_0.8mm']
        values = preset.evaluate_all()

        expected_diameter = 0.8 * 0.65
        assert abs(values['ball_diameter'] - expected_diameter) < 0.001


class TestMLCCPresets:
    """Test MLCC preset functionality."""

    def test_get_all_mlcc_presets(self):
        """Test retrieving all MLCC presets."""
        presets = MLCCPresets.get_all()

        assert len(presets) == 8
        assert 'MLCC_0603' in presets
        assert 'MLCC_0805' in presets
        assert 'MLCC_1206' in presets

    def test_mlcc_0603_dimensions(self):
        """Test MLCC 0603 has correct EIA dimensions."""
        preset = MLCCPresets.get_all()['MLCC_0603']
        values = preset.evaluate_all()

        # EIA 0603: 1.6mm x 0.8mm x 0.8mm
        assert values['body_length'] == 1.6
        assert values['body_width'] == 0.8
        assert values['body_height'] == 0.8

    def test_mlcc_0805_dimensions(self):
        """Test MLCC 0805 has correct EIA dimensions."""
        preset = MLCCPresets.get_all()['MLCC_0805']
        values = preset.evaluate_all()

        # EIA 0805: 2.0mm x 1.25mm x 1.25mm
        assert values['body_length'] == 2.0
        assert values['body_width'] == 1.25
        assert values['body_height'] == 1.25

    def test_mlcc_1206_dimensions(self):
        """Test MLCC 1206 has correct EIA dimensions."""
        preset = MLCCPresets.get_all()['MLCC_1206']
        values = preset.evaluate_all()

        # EIA 1206: 3.2mm x 1.6mm x 1.6mm
        assert values['body_length'] == 3.2
        assert values['body_width'] == 1.6
        assert values['body_height'] == 1.6

    def test_mlcc_termination_width(self):
        """Test MLCC termination width is 90% of body width."""
        preset = MLCCPresets.get_all()['MLCC_0603']
        values = preset.evaluate_all()

        expected_termination = 0.8 * 0.9
        assert abs(values['termination_width'] - expected_termination) < 0.001


class TestResistorPresets:
    """Test Resistor preset functionality."""

    def test_get_all_resistor_presets(self):
        """Test retrieving all resistor presets."""
        presets = ResistorPresets.get_all()

        assert len(presets) == 6
        assert 'RES_0603' in presets
        assert 'RES_0805' in presets

    def test_resistor_0603_dimensions(self):
        """Test resistor 0603 dimensions."""
        preset = ResistorPresets.get_all()['RES_0603']
        values = preset.evaluate_all()

        assert values['body_length'] == 1.6
        assert values['body_width'] == 0.8


class TestPresetLibrary:
    """Test PresetLibrary functionality."""

    def test_preset_library_initialization(self):
        """Test PresetLibrary loads all presets."""
        library = PresetLibrary()

        all_presets = library.list_presets()

        assert len(all_presets) == 21  # 7 BGA + 8 MLCC + 6 Resistor

    def test_filter_presets_by_category(self):
        """Test filtering presets by category."""
        library = PresetLibrary()

        bga_presets = library.list_presets(category='BGA')
        mlcc_presets = library.list_presets(category='MLCC')
        res_presets = library.list_presets(category='RES')

        assert len(bga_presets) == 7
        assert len(mlcc_presets) == 8
        assert len(res_presets) == 6

    def test_get_specific_preset(self):
        """Test retrieving specific preset."""
        library = PresetLibrary()

        preset = library.get('BGA_15x15_0.8mm')

        assert preset is not None
        assert isinstance(preset, ParameterSet)

    def test_get_nonexistent_preset(self):
        """Test retrieving non-existent preset returns None."""
        library = PresetLibrary()

        preset = library.get('NONEXISTENT_PRESET')

        assert preset is None

    def test_add_custom_preset(self):
        """Test adding custom preset to library."""
        library = PresetLibrary()

        from koocad.core.parameters import FloatParameter

        custom = ParameterSet()
        custom.add(FloatParameter(name='width', value=100.0))

        library.add_preset('CUSTOM_TEST', custom)

        retrieved = library.get('CUSTOM_TEST')

        assert retrieved is not None
        assert 'width' in retrieved.parameters

    def test_preset_categories(self):
        """Test all presets are categorized correctly."""
        library = PresetLibrary()

        all_presets = library.list_presets()

        # Check each preset starts with valid category
        valid_categories = ['BGA', 'MLCC', 'RES']

        for preset_name in all_presets:
            category = preset_name.split('_')[0]
            assert category in valid_categories


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
