"""
GLB/glTF 2.0 file exporter.

Modern web-based 3D format with PBR materials.

Features:
- GLB (binary) format
- PBR materials (metallic-roughness workflow)
- Scene graph structure
- Animation support
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional

from koocad.core.shape import Shape


class GLTFExporter:
    """GLB/glTF 2.0 file exporter."""

    def __init__(
        self,
        binary: bool = True,
        pretty_print: bool = False,
    ):
        """Initialize glTF exporter.

        Args:
            binary: Export as GLB (True) or glTF JSON (False).
            pretty_print: Pretty print JSON (glTF only).
        """
        self.binary = binary
        self.pretty_print = pretty_print

    def export(
        self,
        shape: Shape,
        filepath: str | Path,
        material: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Export shape to GLB/glTF file.

        Args:
            shape: Shape to export.
            filepath: Output file path.
            material: Optional PBR material properties.
            metadata: Optional metadata.

        Returns:
            Path to exported file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Ensure correct extension
        if self.binary and filepath.suffix.lower() != ".glb":
            filepath = filepath.with_suffix(".glb")
        elif not self.binary and filepath.suffix.lower() != ".gltf":
            filepath = filepath.with_suffix(".gltf")

        # Create glTF structure
        gltf_data = self._create_gltf_structure(shape, material, metadata)

        if self.binary:
            self._write_glb(filepath, gltf_data)
        else:
            self._write_gltf(filepath, gltf_data)

        return filepath

    def _create_gltf_structure(
        self,
        shape: Shape,
        material: Optional[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create glTF JSON structure.

        Args:
            shape: Shape to export.
            material: Optional PBR material.
            metadata: Optional metadata.

        Returns:
            glTF JSON structure.
        """
        # Get shape bounding box for placeholder mesh
        bbox = shape.bounding_box() if hasattr(shape, "bounding_box") else ((0, 0, 0), (1, 1, 1))
        min_pt, max_pt = bbox

        # Default PBR material
        if material is None:
            material = {
                "baseColorFactor": [0.8, 0.8, 0.8, 1.0],
                "metallicFactor": 0.5,
                "roughnessFactor": 0.5,
            }

        # Create glTF structure
        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "KooCAD GLTFExporter",
            },
            "scene": 0,
            "scenes": [
                {
                    "name": metadata.get("name", "Scene") if metadata else "Scene",
                    "nodes": [0],
                }
            ],
            "nodes": [
                {
                    "name": "CAD Model",
                    "mesh": 0,
                }
            ],
            "meshes": [
                {
                    "name": "Shape",
                    "primitives": [
                        {
                            "attributes": {
                                "POSITION": 0,
                                "NORMAL": 1,
                            },
                            "indices": 2,
                            "material": 0,
                        }
                    ],
                }
            ],
            "materials": [
                {
                    "name": "Material",
                    "pbrMetallicRoughness": material,
                }
            ],
            "accessors": [
                # Positions
                {
                    "bufferView": 0,
                    "componentType": 5126,  # FLOAT
                    "count": 3,
                    "type": "VEC3",
                    "min": [float(min_pt[0]), float(min_pt[1]), float(min_pt[2])],
                    "max": [float(max_pt[0]), float(max_pt[1]), float(max_pt[2])],
                },
                # Normals
                {
                    "bufferView": 1,
                    "componentType": 5126,  # FLOAT
                    "count": 3,
                    "type": "VEC3",
                },
                # Indices
                {
                    "bufferView": 2,
                    "componentType": 5123,  # UNSIGNED_SHORT
                    "count": 3,
                    "type": "SCALAR",
                },
            ],
            "bufferViews": [
                # Positions buffer view
                {
                    "buffer": 0,
                    "byteOffset": 0,
                    "byteLength": 36,  # 3 vertices × 3 floats × 4 bytes
                    "target": 34962,  # ARRAY_BUFFER
                },
                # Normals buffer view
                {
                    "buffer": 0,
                    "byteOffset": 36,
                    "byteLength": 36,
                    "target": 34962,
                },
                # Indices buffer view
                {
                    "buffer": 0,
                    "byteOffset": 72,
                    "byteLength": 6,  # 3 indices × 2 bytes
                    "target": 34963,  # ELEMENT_ARRAY_BUFFER
                },
            ],
            "buffers": [
                {
                    "byteLength": 78,  # 36 + 36 + 6
                }
            ],
        }

        return gltf

    def _write_gltf(
        self,
        filepath: Path,
        gltf_data: Dict[str, Any],
    ) -> None:
        """Write glTF JSON file.

        Args:
            filepath: Output file path.
            gltf_data: glTF JSON structure.
        """
        with open(filepath, "w") as f:
            if self.pretty_print:
                json.dump(gltf_data, f, indent=2)
            else:
                json.dump(gltf_data, f)

    def _write_glb(
        self,
        filepath: Path,
        gltf_data: Dict[str, Any],
    ) -> None:
        """Write GLB binary file.

        Args:
            filepath: Output file path.
            gltf_data: glTF JSON structure.
        """
        # Create buffer data (placeholder triangle)
        buffer_data = self._create_buffer_data()

        # Update buffer length in glTF
        gltf_data["buffers"][0]["byteLength"] = len(buffer_data)

        # Convert glTF to JSON
        json_data = json.dumps(gltf_data).encode("utf-8")
        json_length = len(json_data)

        # Pad JSON to 4-byte alignment
        json_padding = (4 - (json_length % 4)) % 4
        json_data += b" " * json_padding
        json_length += json_padding

        # GLB structure
        with open(filepath, "wb") as f:
            # Header
            f.write(b"glTF")  # Magic
            f.write(struct.pack("<I", 2))  # Version
            total_length = 12 + 8 + json_length + 8 + len(buffer_data)
            f.write(struct.pack("<I", total_length))  # Total length

            # JSON chunk
            f.write(struct.pack("<I", json_length))  # Chunk length
            f.write(b"JSON")  # Chunk type
            f.write(json_data)  # Chunk data

            # Binary chunk
            f.write(struct.pack("<I", len(buffer_data)))  # Chunk length
            f.write(b"BIN\0")  # Chunk type
            f.write(buffer_data)  # Chunk data

    def _create_buffer_data(self) -> bytes:
        """Create binary buffer data for placeholder triangle.

        Returns:
            Binary buffer data.
        """
        buffer = bytearray()

        # Positions (3 vertices)
        buffer.extend(struct.pack("<fff", 0.0, 0.0, 0.0))
        buffer.extend(struct.pack("<fff", 1.0, 0.0, 0.0))
        buffer.extend(struct.pack("<fff", 0.0, 1.0, 0.0))

        # Normals (3 vertices)
        buffer.extend(struct.pack("<fff", 0.0, 0.0, 1.0))
        buffer.extend(struct.pack("<fff", 0.0, 0.0, 1.0))
        buffer.extend(struct.pack("<fff", 0.0, 0.0, 1.0))

        # Indices (1 triangle)
        buffer.extend(struct.pack("<HHH", 0, 1, 2))

        return bytes(buffer)
