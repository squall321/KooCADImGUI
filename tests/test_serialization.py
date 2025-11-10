"""
Pytest test suite for KooCAD serialization module.

Tests for parameter and parameter set serialization/deserialization.
"""

import pytest
from koocad.core.serialization import ParameterSerializer
from koocad.core.parameters import (
    FloatParameter,
    IntParameter,
    StringParameter,
    ExpressionParameter,
    ParameterSet,
    Unit,
)


class TestParameterSerialization:
    """Test parameter serialization."""

    def test_float_parameter_to_dict(self):
        """Test FloatParameter serialization to dict."""
        fp = FloatParameter(
            name='width',
            value=10.0,
            min_value=0.0,
            max_value=100.0,
            unit=Unit.MM,
            description='Test width parameter'
        )

        data = ParameterSerializer.parameter_to_dict(fp)

        assert data['type'] == 'FloatParameter'
        assert data['name'] == 'width'
        assert data['value'] == 10.0
        assert data['min_value'] == 0.0
        assert data['max_value'] == 100.0
        assert data['description'] == 'Test width parameter'

    def test_int_parameter_to_dict(self):
        """Test IntParameter serialization to dict."""
        ip = IntParameter(
            name='count',
            value=15,
            min_value=1,
            max_value=50
        )

        data = ParameterSerializer.parameter_to_dict(ip)

        assert data['type'] == 'IntParameter'
        assert data['name'] == 'count'
        assert data['value'] == 15
        assert data['min_value'] == 1
        assert data['max_value'] == 50

    def test_roundtrip_serialization(self):
        """Test parameter roundtrip serialization."""
        original = FloatParameter(
            name='height',
            value=20.0,
            min_value=0.0,
            max_value=100.0
        )

        # Serialize
        data = ParameterSerializer.parameter_to_dict(original)

        # Deserialize
        restored = ParameterSerializer.dict_to_parameter(data)

        # Verify
        assert restored.name == original.name
        assert restored.value == original.value
        assert restored.min_value == original.min_value
        assert restored.max_value == original.max_value


class TestParameterSetSerialization:
    """Test ParameterSet serialization."""

    def test_parameter_set_to_dict(self):
        """Test ParameterSet serialization to dict."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name='width', value=10.0))
        param_set.add(FloatParameter(name='height', value=20.0))

        data = ParameterSerializer.parameter_set_to_dict(param_set)

        assert 'parameters' in data
        assert 'version' in data
        # parameters is a list, not a dict
        assert isinstance(data['parameters'], list)
        assert len(data['parameters']) == 2
        
        # Check parameter names
        param_names = [p['name'] for p in data['parameters']]
        assert 'width' in param_names
        assert 'height' in param_names

    def test_parameter_set_roundtrip(self):
        """Test ParameterSet roundtrip serialization."""
        original = ParameterSet()
        original.add(FloatParameter(name='width', value=10.0))
        original.add(IntParameter(name='count', value=15))
        original.add(ExpressionParameter(name='expr', value='width + 10'))

        # Serialize
        data = ParameterSerializer.parameter_set_to_dict(original)

        # Deserialize
        restored = ParameterSerializer.dict_to_parameter_set(data)

        # Verify
        assert len(restored.parameters) == len(original.parameters)
        assert restored.get('width').value == original.get('width').value
        assert restored.get('count').value == original.get('count').value
        assert restored.get('expr').value == original.get('expr').value

    def test_parameter_set_with_expressions(self):
        """Test ParameterSet with ExpressionParameters."""
        param_set = ParameterSet()
        param_set.add(FloatParameter(name='width', value=10.0))
        param_set.add(FloatParameter(name='height', value=20.0))
        param_set.add(ExpressionParameter(name='area', value='width * height'))

        # Serialize
        data = ParameterSerializer.parameter_set_to_dict(param_set)

        # Deserialize
        restored = ParameterSerializer.dict_to_parameter_set(data)

        # Verify
        assert len(restored.parameters) == 3
        assert isinstance(restored.get('area'), ExpressionParameter)
        assert restored.get('area').value == 'width * height'


class TestSerializationEdgeCases:
    """Test serialization edge cases."""

    def test_parameter_with_no_constraints(self):
        """Test parameter without min/max constraints."""
        fp = FloatParameter(name='value', value=42.0)

        data = ParameterSerializer.parameter_to_dict(fp)
        restored = ParameterSerializer.dict_to_parameter(data)

        assert restored.value == 42.0
        assert restored.min_value is None
        assert restored.max_value is None

    def test_empty_parameter_set(self):
        """Test empty ParameterSet serialization."""
        empty_set = ParameterSet()

        data = ParameterSerializer.parameter_set_to_dict(empty_set)
        restored = ParameterSerializer.dict_to_parameter_set(data)

        assert len(restored.parameters) == 0


# Run tests with pytest
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
