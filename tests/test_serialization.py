"""
Tests for parameter serialization.
"""

import json
from pathlib import Path

import pytest

from koocad.core.parameters import FloatParameter, IntParameter, ParameterSet, Unit
from koocad.core.serialization import (
    JSONSerializer,
    ParameterSerializer,
    SerializationFormat,
    UniversalSerializer,
)


def test_parameter_to_dict():
    """Test parameter to dictionary conversion."""
    param = FloatParameter(
        name="width",
        value=12.0,
        description="Width in mm",
        min_value=5.0,
        max_value=50.0,
        unit=Unit.MM,
    )

    data = ParameterSerializer.parameter_to_dict(param)

    assert data["name"] == "width"
    assert data["value"] == 12.0
    assert data["type"] == "FloatParameter"
    assert data["min_value"] == 5.0
    assert data["max_value"] == 50.0
    assert data["unit"] == "mm"


def test_dict_to_parameter():
    """Test dictionary to parameter conversion."""
    data = {
        "type": "FloatParameter",
        "name": "width",
        "value": 12.0,
        "description": "Width in mm",
        "min_value": 5.0,
        "max_value": 50.0,
        "unit": "mm",
    }

    param = ParameterSerializer.dict_to_parameter(data)

    assert isinstance(param, FloatParameter)
    assert param.name == "width"
    assert param.value == 12.0
    assert param.min_value == 5.0
    assert param.max_value == 50.0
    assert param.unit == Unit.MM


def test_parameter_set_serialization():
    """Test parameter set serialization."""
    param_set = ParameterSet()
    param_set.add(
        FloatParameter(
            name="width",
            value=12.0,
            min_value=5.0,
            max_value=50.0,
            unit=Unit.MM,
        )
    )
    param_set.add(
        IntParameter(
            name="count",
            value=10,
            min_value=1,
            max_value=100,
        )
    )

    # Serialize
    json_str = JSONSerializer.serialize(param_set)
    assert "width" in json_str
    assert "count" in json_str

    # Deserialize
    restored = JSONSerializer.deserialize(json_str)
    assert len(restored.parameters) == 2
    assert restored.get("width") is not None
    assert restored.get("count") is not None


def test_json_file_operations(tmp_path: Path):
    """Test JSON save/load operations."""
    param_set = ParameterSet()
    param_set.add(
        FloatParameter(
            name="width",
            value=12.0,
            unit=Unit.MM,
        )
    )

    file_path = tmp_path / "params.json"

    # Save
    JSONSerializer.save(param_set, file_path)
    assert file_path.exists()

    # Load
    loaded = JSONSerializer.load(file_path)
    assert len(loaded.parameters) == 1
    assert loaded.get("width") is not None


def test_universal_serializer_auto_detect(tmp_path: Path):
    """Test universal serializer format auto-detection."""
    param_set = ParameterSet()
    param_set.add(
        FloatParameter(
            name="width",
            value=12.0,
            unit=Unit.MM,
        )
    )

    # Test .json extension
    json_file = tmp_path / "params.json"
    UniversalSerializer.save(param_set, json_file)
    loaded = UniversalSerializer.load(json_file)
    assert loaded.get("width") is not None


def test_roundtrip_preserves_values():
    """Test that serialization roundtrip preserves all values."""
    param_set = ParameterSet()
    param_set.add(
        FloatParameter(
            name="width",
            value=12.345,
            description="Test parameter",
            min_value=5.0,
            max_value=50.0,
            unit=Unit.MM,
        )
    )
    param_set.add(
        IntParameter(
            name="count",
            value=42,
            description="Count parameter",
            min_value=1,
            max_value=100,
        )
    )

    # Serialize and deserialize
    json_str = JSONSerializer.serialize(param_set)
    restored = JSONSerializer.deserialize(json_str)

    # Check width
    width = restored.get("width")
    assert isinstance(width, FloatParameter)
    assert width.value == 12.345
    assert width.min_value == 5.0
    assert width.max_value == 50.0
    assert width.unit == Unit.MM

    # Check count
    count = restored.get("count")
    assert isinstance(count, IntParameter)
    assert count.value == 42
    assert count.min_value == 1
    assert count.max_value == 100


@pytest.mark.skipif(
    not pytest.importorskip("msgpack", reason="msgpack not installed"),
    reason="msgpack not installed",
)
def test_messagepack_serialization():
    """Test MessagePack serialization."""
    from koocad.core.serialization import MessagePackSerializer

    param_set = ParameterSet()
    param_set.add(
        FloatParameter(
            name="width",
            value=12.0,
            unit=Unit.MM,
        )
    )

    # Serialize
    data = MessagePackSerializer.serialize(param_set)
    assert isinstance(data, bytes)

    # Deserialize
    restored = MessagePackSerializer.deserialize(data)
    assert restored.get("width") is not None
