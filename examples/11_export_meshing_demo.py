#!/usr/bin/env python
"""
KooCAD Export & Meshing Pipeline Demo.

This example demonstrates the complete export and meshing workflow:
- Export to multiple CAD formats (STEP, IGES, STL, GLB, OBJ)
- Gmsh meshing integration
- LS-DYNA keyword file generation
- Mesh quality analysis

Phase 121-135 Complete:
- STEP exporter (AP214)
- IGES exporter
- STL exporter (binary/ASCII)
- GLB/glTF 2.0 exporter with PBR materials
- OBJ/MTL exporter
- Gmsh mesher integration
- LS-DYNA keyword generator
- Mesh quality checker

Requirements:
    pip install cadquery  # For actual CAD generation
    pip install gmsh  # For mesh generation (optional)

Usage:
    python examples/11_export_meshing_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def demo_export():
    """Demonstrate export to various formats."""
    print("=" * 70)
    print("Export Pipeline Demo")
    print("=" * 70)

    try:
        # Create a simple BGA package
        from koocad.generators.bga import BGAGenerator

        print("\n1. Generating BGA package...")
        generator = BGAGenerator(
            substrate_width=12.0,
            substrate_height=12.0,
            substrate_thickness=0.8,
            ball_rows=10,
            ball_cols=10,
            ball_pitch=0.8,
            ball_diameter=0.4,
        )
        shape = generator.generate()
        print(f"   ✓ Generated BGA: {shape.volume():.2f} mm³")

    except ImportError:
        print("\n1. CadQuery not installed - using placeholder shapes")
        from koocad.core.shape import Shape
        shape = Shape()
        print("   ⚠ Using placeholder shape")

    # Export to various formats
    output_dir = Path("output/exports")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n2. Exporting to CAD formats...")

    # STEP export
    from koocad.exporters.step import STEPExporter
    step_exporter = STEPExporter(schema="AP214", author="KooCAD Demo")
    step_file = step_exporter.export(
        shape,
        output_dir / "bga.step",
        metadata={"title": "BGA Package", "description": "10x10 BGA package"},
    )
    print(f"   ✓ STEP: {step_file}")

    # IGES export
    from koocad.exporters.iges import IGESExporter
    iges_exporter = IGESExporter(representation="BREP")
    iges_file = iges_exporter.export(shape, output_dir / "bga.iges")
    print(f"   ✓ IGES: {iges_file}")

    # STL export (binary)
    from koocad.exporters.stl import STLExporter
    stl_exporter = STLExporter(binary=True, resolution=0.1)
    stl_file = stl_exporter.export(shape, output_dir / "bga.stl")
    tri_count = stl_exporter.get_triangle_count(shape)
    print(f"   ✓ STL:  {stl_file} (~{tri_count} triangles)")

    # GLB export
    from koocad.exporters.gltf import GLTFExporter
    gltf_exporter = GLTFExporter(binary=True)
    glb_file = gltf_exporter.export(
        shape,
        output_dir / "bga.glb",
        material={
            "baseColorFactor": [0.2, 0.2, 0.2, 1.0],
            "metallicFactor": 0.8,
            "roughnessFactor": 0.3,
        },
    )
    print(f"   ✓ GLB:  {glb_file}")

    # OBJ export
    from koocad.exporters.obj import OBJExporter
    obj_exporter = OBJExporter(export_materials=True, export_normals=True)
    obj_file = obj_exporter.export(
        shape,
        output_dir / "bga.obj",
        material={
            "diffuse": (0.8, 0.8, 0.8),
            "specular": (0.5, 0.5, 0.5),
            "shininess": 32.0,
        },
    )
    print(f"   ✓ OBJ:  {obj_file}")
    print(f"   ✓ MTL:  {output_dir / 'bga.mtl'}")


def demo_meshing():
    """Demonstrate meshing with Gmsh."""
    print("\n" + "=" * 70)
    print("Meshing Pipeline Demo")
    print("=" * 70)

    try:
        from koocad.generators.bga import BGAGenerator
        from koocad.core.shape import Shape

        shape = Shape()  # Placeholder
    except:
        from koocad.core.shape import Shape
        shape = Shape()

    output_dir = Path("output/mesh")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n1. Gmsh meshing...")
    from koocad.meshing.gmsh_mesher import GmshMesher

    mesher = GmshMesher(
        element_size=0.5,
        element_type="tet10",
        algorithm=6,
    )

    try:
        node_count, elem_count = mesher.mesh(
            shape,
            output_dir / "bga.msh",
        )
        print(f"   ✓ Mesh generated:")
        print(f"     - Nodes: {node_count}")
        print(f"     - Elements: {elem_count}")
        print(f"     - Element type: tet10")
        print(f"     - File: {output_dir / 'bga.msh'}")
    except Exception as e:
        print(f"   ⚠ Gmsh not available: {e}")
        print(f"     Install with: pip install gmsh")


def demo_lsdyna():
    """Demonstrate LS-DYNA keyword file generation."""
    print("\n" + "=" * 70)
    print("LS-DYNA Keyword Generator Demo")
    print("=" * 70)

    from koocad.meshing.lsdyna import LSDYNAKeywordGenerator

    # Create keyword file
    print("\n1. Creating LS-DYNA keyword file...")
    lsdyna = LSDYNAKeywordGenerator()

    # Add material (Steel)
    lsdyna.add_material(
        material_id=1,
        mat_type="ELASTIC",
        density=7.85e-9,  # tonne/mm^3
        youngs_modulus=210000.0,  # MPa
        poisson_ratio=0.3,
    )

    # Add part
    lsdyna.add_part(
        part_id=1,
        section_id=1,
        material_id=1,
        name="BGA_Substrate",
    )

    # Add sample nodes (8-node brick)
    nodes = [
        (1, 0.0, 0.0, 0.0),
        (2, 12.0, 0.0, 0.0),
        (3, 12.0, 12.0, 0.0),
        (4, 0.0, 12.0, 0.0),
        (5, 0.0, 0.0, 0.8),
        (6, 12.0, 0.0, 0.8),
        (7, 12.0, 12.0, 0.8),
        (8, 0.0, 12.0, 0.8),
    ]

    for node_id, x, y, z in nodes:
        lsdyna.add_node(node_id, x, y, z)

    # Add element
    lsdyna.add_element(
        element_id=1,
        part_id=1,
        node_ids=[1, 2, 3, 4, 5, 6, 7, 8],
    )

    # Write keyword file
    output_dir = Path("output/lsdyna")
    output_dir.mkdir(parents=True, exist_ok=True)
    keyword_file = lsdyna.write(
        output_dir / "bga.k",
        title="BGA Package - Drop Test",
    )

    print(f"   ✓ Keyword file: {keyword_file}")
    print(f"     - Nodes: {len(nodes)}")
    print(f"     - Elements: 1")
    print(f"     - Parts: 1")
    print(f"     - Materials: 1")


def demo_quality():
    """Demonstrate mesh quality analysis."""
    print("\n" + "=" * 70)
    print("Mesh Quality Analysis Demo")
    print("=" * 70)

    from koocad.meshing.quality import MeshQualityChecker

    # Create sample mesh (tetrahedral element)
    print("\n1. Analyzing mesh quality...")
    nodes = [
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.5, 1.0, 0.0),
        (0.5, 0.5, 1.0),
    ]

    elements = [[0, 1, 2, 3]]  # Tetrahedral element

    checker = MeshQualityChecker()

    # Check aspect ratio
    aspect = checker.check_aspect_ratio(nodes, elements)
    print(f"\n   Aspect Ratio:")
    print(f"     - Min:  {aspect['min']:.6f}")
    print(f"     - Max:  {aspect['max']:.6f}")
    print(f"     - Mean: {aspect['mean']:.6f}")

    # Check Jacobian
    jacobian = checker.check_jacobian(nodes, elements)
    print(f"\n   Jacobian:")
    print(f"     - Min:  {jacobian['min']:.6f}")
    print(f"     - Max:  {jacobian['max']:.6f}")
    print(f"     - Negative count: {jacobian['negative_count']}")

    # Generate report
    report = checker.generate_report()
    print(f"\n{report}")


def main():
    """Run all demos."""
    print("=" * 70)
    print("KooCAD Export & Meshing Pipeline Demo")
    print("=" * 70)
    print("\nPhase 121-135 Complete:")
    print("  ✓ STEP/IGES/STL/GLB/OBJ exporters")
    print("  ✓ Gmsh meshing integration")
    print("  ✓ LS-DYNA keyword generator")
    print("  ✓ Mesh quality analysis")
    print("\nProgress: 135/145 phases (93.1%)")
    print("=" * 70)

    # Run demos
    demo_export()
    demo_meshing()
    demo_lsdyna()
    demo_quality()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nOutput files created in:")
    print("  - output/exports/  (CAD files)")
    print("  - output/mesh/     (Mesh files)")
    print("  - output/lsdyna/   (LS-DYNA keywords)")
    print("\nNext Steps (Phase 136-145):")
    print("  - HPC batch system (Slurm)")
    print("  - Apptainer container orchestration")
    print("  - Parallel parameter sweeps")
    print("  - MinIO data lake integration")
    print("=" * 70)


if __name__ == "__main__":
    main()
