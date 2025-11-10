#!/usr/bin/env python
"""
KooCAD UI Demo.

This example launches the KooCAD graphical user interface.
Run this to see the node-based parametric CAD system in action.

Requirements:
    pip install dearpygui

Usage:
    python examples/08_ui_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from koocad.ui.app import KooCADApp

    def main():
        """Launch KooCAD UI."""
        print("=" * 70)
        print("KooCAD - Parametric Electronic Component CAD")
        print("=" * 70)
        print("\nLaunching UI...")
        print("\nFeatures:")
        print("  - Node-based visual programming")
        print("  - Parametric component design")
        print("  - Real-time 3D preview")
        print("  - Export to STEP/STL/IGES")
        print("\nControls:")
        print("  - Drag from Component Library to add nodes")
        print("  - Click and drag between pins to create links")
        print("  - Right-click on nodes to delete")
        print("  - Use menu bar for file operations")
        print("\n" + "=" * 70)

        app = KooCADApp()
        app.run()

except ImportError as e:
    print("Error: DearPyGui is not installed.")
    print("\nTo install DearPyGui, run:")
    print("  pip install dearpygui")
    print("\nOr install with all UI dependencies:")
    print("  pip install koocad[gui]")
    print(f"\nDetails: {e}")
    sys.exit(1)


if __name__ == "__main__":
    main()
