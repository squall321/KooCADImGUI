"""
Parameter serialization support for JSON, MessagePack, and Protocol Buffers.

This module provides efficient serialization and deserialization of parameters
for storage, transmission, and HPC batch processing.
"""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar

try:
    import msgpack
except ImportError:
    msgpack = None  # type: ignore

try:
    from google.protobuf import json_format
    from google.protobuf.message import Message as ProtoMessage
except ImportError:
    json_format = None  # type: ignore
    ProtoMessage = None  # type: ignore

from koocad.core.parameters import (
    ExpressionParameter,
    FloatParameter,
    IntParameter,
    Parameter,
    ParameterSet,
    StringParameter,
    Unit,
)

T = TypeVar("T")


class SerializationFormat(Enum):
    """Supported serialization formats."""

    JSON = "json"
    MESSAGEPACK = "msgpack"
    PROTOBUF = "protobuf"


class ParameterSerializer:
    """Serialize and deserialize parameters."""

    @staticmethod
    def parameter_to_dict(param: Parameter) -> dict[str, Any]:
        """Convert parameter to dictionary.

        Args:
            param: Parameter to serialize.

        Returns:
            Dictionary representation.
        """
        base_dict = {
            "type": param.__class__.__name__,
            "name": param.name,
            "value": param.value,
            "description": param.description,
        }

        # Add type-specific fields
        if isinstance(param, FloatParameter):
            base_dict.update(
                {
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                    "unit": param.unit.value if param.unit else None,
                }
            )
        elif isinstance(param, IntParameter):
            base_dict.update(
                {
                    "min_value": param.min_value,
                    "max_value": param.max_value,
                }
            )
        elif isinstance(param, ExpressionParameter):
            base_dict.update(
                {
                    "dependencies": param.dependencies,
                }
            )

        return base_dict

    @staticmethod
    def dict_to_parameter(data: dict[str, Any]) -> Parameter:
        """Convert dictionary to parameter.

        Args:
            data: Dictionary representation.

        Returns:
            Reconstructed parameter.

        Raises:
            ValueError: If parameter type is unknown.
        """
        param_type = data.get("type")
        name = data["name"]
        value = data["value"]
        description = data.get("description", "")

        if param_type == "FloatParameter":
            return FloatParameter(
                name=name,
                value=float(value),
                description=description,
                min_value=data.get("min_value"),
                max_value=data.get("max_value"),
                unit=Unit(data["unit"]) if data.get("unit") else Unit.MM,
            )
        elif param_type == "IntParameter":
            return IntParameter(
                name=name,
                value=int(value),
                description=description,
                min_value=data.get("min_value"),
                max_value=data.get("max_value"),
            )
        elif param_type == "StringParameter":
            return StringParameter(
                name=name,
                value=str(value),
                description=description,
            )
        elif param_type == "ExpressionParameter":
            return ExpressionParameter(
                name=name,
                value=str(value),
                description=description,
                dependencies=data.get("dependencies", []),
            )
        else:
            raise ValueError(f"Unknown parameter type: {param_type}")

    @staticmethod
    def parameter_set_to_dict(param_set: ParameterSet) -> dict[str, Any]:
        """Convert parameter set to dictionary.

        Args:
            param_set: ParameterSet to serialize.

        Returns:
            Dictionary representation.
        """
        return {
            "parameters": [
                ParameterSerializer.parameter_to_dict(param)
                for param in param_set.parameters.values()
            ],
            "version": "1.0",
        }

    @staticmethod
    def dict_to_parameter_set(data: dict[str, Any]) -> ParameterSet:
        """Convert dictionary to parameter set.

        Args:
            data: Dictionary representation.

        Returns:
            Reconstructed parameter set.
        """
        param_set = ParameterSet()

        for param_data in data.get("parameters", []):
            param = ParameterSerializer.dict_to_parameter(param_data)
            param_set.add(param)

        return param_set


class JSONSerializer:
    """JSON serialization."""

    @staticmethod
    def serialize(param_set: ParameterSet, indent: int = 2) -> str:
        """Serialize parameter set to JSON string.

        Args:
            param_set: ParameterSet to serialize.
            indent: JSON indentation (default: 2 for human-readable).

        Returns:
            JSON string.
        """
        data = ParameterSerializer.parameter_set_to_dict(param_set)
        return json.dumps(data, indent=indent)

    @staticmethod
    def deserialize(json_str: str) -> ParameterSet:
        """Deserialize parameter set from JSON string.

        Args:
            json_str: JSON string.

        Returns:
            Reconstructed parameter set.
        """
        data = json.loads(json_str)
        return ParameterSerializer.dict_to_parameter_set(data)

    @staticmethod
    def save(param_set: ParameterSet, file_path: str | Path) -> None:
        """Save parameter set to JSON file.

        Args:
            param_set: ParameterSet to save.
            file_path: Path to output file.
        """
        path = Path(file_path)
        path.write_text(JSONSerializer.serialize(param_set))

    @staticmethod
    def load(file_path: str | Path) -> ParameterSet:
        """Load parameter set from JSON file.

        Args:
            file_path: Path to input file.

        Returns:
            Loaded parameter set.
        """
        path = Path(file_path)
        return JSONSerializer.deserialize(path.read_text())


class MessagePackSerializer:
    """MessagePack binary serialization (compact for network transmission)."""

    @staticmethod
    def serialize(param_set: ParameterSet) -> bytes:
        """Serialize parameter set to MessagePack bytes.

        Args:
            param_set: ParameterSet to serialize.

        Returns:
            MessagePack bytes.

        Raises:
            ImportError: If msgpack is not installed.
        """
        if msgpack is None:
            raise ImportError("msgpack-python is required for MessagePack serialization")

        data = ParameterSerializer.parameter_set_to_dict(param_set)
        return msgpack.packb(data, use_bin_type=True)

    @staticmethod
    def deserialize(data: bytes) -> ParameterSet:
        """Deserialize parameter set from MessagePack bytes.

        Args:
            data: MessagePack bytes.

        Returns:
            Reconstructed parameter set.

        Raises:
            ImportError: If msgpack is not installed.
        """
        if msgpack is None:
            raise ImportError("msgpack-python is required for MessagePack deserialization")

        unpacked = msgpack.unpackb(data, raw=False)
        return ParameterSerializer.dict_to_parameter_set(unpacked)

    @staticmethod
    def save(param_set: ParameterSet, file_path: str | Path) -> None:
        """Save parameter set to MessagePack file.

        Args:
            param_set: ParameterSet to save.
            file_path: Path to output file.
        """
        path = Path(file_path)
        path.write_bytes(MessagePackSerializer.serialize(param_set))

    @staticmethod
    def load(file_path: str | Path) -> ParameterSet:
        """Load parameter set from MessagePack file.

        Args:
            file_path: Path to input file.

        Returns:
            Loaded parameter set.
        """
        path = Path(file_path)
        return MessagePackSerializer.deserialize(path.read_bytes())


class ProtobufSerializer:
    """Protocol Buffers serialization (for gRPC APIs)."""

    # TODO: Generate .proto files and Python bindings in Phase 106-120
    # For now, use JSON format as protobuf representation

    @staticmethod
    def serialize(param_set: ParameterSet) -> bytes:
        """Serialize parameter set to Protocol Buffers bytes.

        Args:
            param_set: ParameterSet to serialize.

        Returns:
            Protobuf bytes (currently JSON-based).

        Note:
            Full protobuf support will be implemented in Phase 106-120.
        """
        # Placeholder: use JSON encoding
        json_str = JSONSerializer.serialize(param_set)
        return json_str.encode("utf-8")

    @staticmethod
    def deserialize(data: bytes) -> ParameterSet:
        """Deserialize parameter set from Protocol Buffers bytes.

        Args:
            data: Protobuf bytes (currently JSON-based).

        Returns:
            Reconstructed parameter set.
        """
        # Placeholder: use JSON decoding
        json_str = data.decode("utf-8")
        return JSONSerializer.deserialize(json_str)


class UniversalSerializer:
    """Universal serializer supporting multiple formats."""

    @staticmethod
    def serialize(
        param_set: ParameterSet,
        format: SerializationFormat = SerializationFormat.JSON,
    ) -> str | bytes:
        """Serialize parameter set in specified format.

        Args:
            param_set: ParameterSet to serialize.
            format: Serialization format.

        Returns:
            Serialized data (str for JSON, bytes for binary formats).
        """
        if format == SerializationFormat.JSON:
            return JSONSerializer.serialize(param_set)
        elif format == SerializationFormat.MESSAGEPACK:
            return MessagePackSerializer.serialize(param_set)
        elif format == SerializationFormat.PROTOBUF:
            return ProtobufSerializer.serialize(param_set)
        else:
            raise ValueError(f"Unknown serialization format: {format}")

    @staticmethod
    def deserialize(
        data: str | bytes,
        format: SerializationFormat = SerializationFormat.JSON,
    ) -> ParameterSet:
        """Deserialize parameter set from specified format.

        Args:
            data: Serialized data.
            format: Serialization format.

        Returns:
            Reconstructed parameter set.
        """
        if format == SerializationFormat.JSON:
            return JSONSerializer.deserialize(data)  # type: ignore
        elif format == SerializationFormat.MESSAGEPACK:
            return MessagePackSerializer.deserialize(data)  # type: ignore
        elif format == SerializationFormat.PROTOBUF:
            return ProtobufSerializer.deserialize(data)  # type: ignore
        else:
            raise ValueError(f"Unknown serialization format: {format}")

    @staticmethod
    def save(
        param_set: ParameterSet,
        file_path: str | Path,
        format: SerializationFormat | None = None,
    ) -> None:
        """Save parameter set to file.

        Args:
            param_set: ParameterSet to save.
            file_path: Path to output file.
            format: Serialization format (auto-detect from extension if None).
        """
        path = Path(file_path)

        # Auto-detect format from extension
        if format is None:
            ext = path.suffix.lower()
            if ext == ".json":
                format = SerializationFormat.JSON
            elif ext in (".msgpack", ".mp"):
                format = SerializationFormat.MESSAGEPACK
            elif ext in (".pb", ".protobuf"):
                format = SerializationFormat.PROTOBUF
            else:
                format = SerializationFormat.JSON  # Default

        # Serialize and save
        if format == SerializationFormat.JSON:
            JSONSerializer.save(param_set, path)
        elif format == SerializationFormat.MESSAGEPACK:
            MessagePackSerializer.save(param_set, path)
        elif format == SerializationFormat.PROTOBUF:
            data = ProtobufSerializer.serialize(param_set)
            path.write_bytes(data)

    @staticmethod
    def load(
        file_path: str | Path,
        format: SerializationFormat | None = None,
    ) -> ParameterSet:
        """Load parameter set from file.

        Args:
            file_path: Path to input file.
            format: Serialization format (auto-detect from extension if None).

        Returns:
            Loaded parameter set.
        """
        path = Path(file_path)

        # Auto-detect format from extension
        if format is None:
            ext = path.suffix.lower()
            if ext == ".json":
                format = SerializationFormat.JSON
            elif ext in (".msgpack", ".mp"):
                format = SerializationFormat.MESSAGEPACK
            elif ext in (".pb", ".protobuf"):
                format = SerializationFormat.PROTOBUF
            else:
                format = SerializationFormat.JSON  # Default

        # Load and deserialize
        if format == SerializationFormat.JSON:
            return JSONSerializer.load(path)
        elif format == SerializationFormat.MESSAGEPACK:
            return MessagePackSerializer.load(path)
        elif format == SerializationFormat.PROTOBUF:
            data = path.read_bytes()
            return ProtobufSerializer.deserialize(data)
        else:
            raise ValueError(f"Unknown format: {format}")
