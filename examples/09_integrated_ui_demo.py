#!/usr/bin/env python
"""
KooCAD Integrated UI Demo with Graph Execution.

This example demonstrates the complete node-based UI system with:
- Component library and node editor
- Graph execution engine with topological sort
- 3D preview viewport (placeholder)
- Real-time parameter updates

The workflow:
1. Add component nodes from the library (left panel)
2. Adjust parameters using sliders in the nodes
3. Connect nodes by dragging between pins
4. Click "Execute Graph" to generate the CAD model
5. View shape info in the 3D preview panel (right panel)

Requirements:
    pip install dearpygui

Note: Actual CAD generation requires CadQuery:
    pip install cadquery

Usage:
    python examples/09_integrated_ui_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from koocad.ui.app import KooCADApp

    def main():
        """Launch integrated KooCAD UI demo."""
        print("=" * 70)
        print("KooCAD - Integrated Parametric CAD UI")
        print("=" * 70)
        print("\nPhase 101-105 Complete: Graph Execution & 3D Preview")
        print("\nFeatures:")
        print("  ✓ Node-based visual programming")
        print("  ✓ Graph execution engine with topological sort")
        print("  ✓ Parameter node connections")
        print("  ✓ 3D preview with shape info (volume, area, bbox)")
        print("  ✓ Real-time execution callback")
        print("\nWorkflow:")
        print("  1. Add component nodes from left panel or Components menu")
        print("  2. Adjust parameters using sliders in nodes")
        print("  3. (Optional) Add parameter nodes and connect to inputs")
        print("  4. Click 'Execute Graph' button in right panel")
        print("  5. View generated shape info in 3D Preview section")
        print("\nSupported Components:")
        print("  - BGA: Ball Grid Array package")
        print("  - MLCC: Multilayer Ceramic Capacitor")
        print("  - Resistor: Chip resistor")
        print("  - More components available in menus")
        print("\nNote:")
        print("  - CadQuery required for actual shape generation")
        print("  - 3D rendering placeholder (shows shape info only)")
        print("  - Full mesh rendering in future phases")
        print("\n" + "=" * 70)

        app = KooCADApp()
        app.run()

except ImportError as e:
    print("Error: DearPyGui is not installed.")
    print("\nTo install DearPyGui, run:")
    print("  pip install dearpygui")
    print("\nFor full functionality including CAD generation:")
    print("  pip install cadquery")
    print(f"\nDetails: {e}")
    sys.exit(1)


if __name__ == "__main__":
    main()
