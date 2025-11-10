"""
Main KooCAD application window.

This module provides the main DearPyGui application window with
menu bar, node editor, and 3D preview.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    dpg = None  # type: ignore

from koocad.ui.node_editor import NodeEditor
from koocad.ui.theme import setup_theme


class KooCADApp:
    """Main KooCAD application."""

    def __init__(self, title: str = "KooCAD - Parametric Electronic Component CAD") -> None:
        """Initialize KooCAD application.

        Args:
            title: Window title.
        """
        if dpg is None:
            raise ImportError("DearPyGui is required. Install with: pip install dearpygui")

        self.title = title
        self.node_editor: Optional[NodeEditor] = None
        self.current_file: Optional[Path] = None

        # Initialize DearPyGui context
        dpg.create_context()

    def setup_fonts(self) -> None:
        """Setup fonts including Korean support."""
        # Add default font
        with dpg.font_registry():
            # Default font for English
            default_font = dpg.add_font("fonts/Roboto-Regular.ttf", 16)

            # Korean font (if available)
            # korean_font = dpg.add_font("fonts/NanumGothic.ttf", 16,
            #     glyph_ranges=dpg.mvFontRangeHint_Korean)

        dpg.bind_font(default_font)

    def create_menu_bar(self) -> None:
        """Create main menu bar."""
        with dpg.menu_bar():
            # File menu
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="New", callback=self.on_new)
                dpg.add_menu_item(label="Open...", callback=self.on_open)
                dpg.add_menu_item(label="Save", callback=self.on_save)
                dpg.add_menu_item(label="Save As...", callback=self.on_save_as)
                dpg.add_separator()
                dpg.add_menu_item(label="Export STEP...", callback=self.on_export_step)
                dpg.add_menu_item(label="Export STL...", callback=self.on_export_stl)
                dpg.add_separator()
                dpg.add_menu_item(label="Exit", callback=self.on_exit)

            # Edit menu
            with dpg.menu(label="Edit"):
                dpg.add_menu_item(label="Undo", callback=self.on_undo)
                dpg.add_menu_item(label="Redo", callback=self.on_redo)
                dpg.add_separator()
                dpg.add_menu_item(label="Delete Selected", callback=self.on_delete)

            # View menu
            with dpg.menu(label="View"):
                dpg.add_menu_item(label="Reset Zoom", callback=self.on_reset_zoom)
                dpg.add_menu_item(label="Fit to Window", callback=self.on_fit_window)
                dpg.add_separator()
                dpg.add_menu_item(label="Show Grid", callback=self.on_toggle_grid, check=True)
                dpg.add_menu_item(label="Dark Theme", callback=self.on_toggle_theme, check=True)

            # Components menu
            with dpg.menu(label="Components"):
                with dpg.menu(label="IC Packages"):
                    dpg.add_menu_item(label="BGA", callback=lambda: self.add_component_node("BGA"))
                    dpg.add_menu_item(label="QFP", callback=lambda: self.add_component_node("QFP"))
                    dpg.add_menu_item(label="SOIC", callback=lambda: self.add_component_node("SOIC"))
                    dpg.add_menu_item(label="DIP", callback=lambda: self.add_component_node("DIP"))

                with dpg.menu(label="Passives"):
                    dpg.add_menu_item(label="MLCC", callback=lambda: self.add_component_node("MLCC"))
                    dpg.add_menu_item(label="Resistor", callback=lambda: self.add_component_node("Resistor"))
                    dpg.add_menu_item(label="Inductor", callback=lambda: self.add_component_node("Inductor"))

                with dpg.menu(label="Connectors"):
                    dpg.add_menu_item(label="Pin Header", callback=lambda: self.add_component_node("PinHeader"))
                    dpg.add_menu_item(label="USB", callback=lambda: self.add_component_node("USB"))
                    dpg.add_menu_item(label="RJ45", callback=lambda: self.add_component_node("RJ45"))

            # Help menu
            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="Documentation", callback=self.on_show_docs)
                dpg.add_menu_item(label="About", callback=self.on_show_about)

    def create_ui(self) -> None:
        """Create main UI layout."""
        with dpg.window(tag="primary_window"):
            self.create_menu_bar()

            # Main horizontal layout
            with dpg.group(horizontal=True):
                # Left panel - Component library
                with dpg.child_window(width=250, tag="library_panel"):
                    dpg.add_text("Component Library", color=(255, 255, 0))
                    dpg.add_separator()

                    # Component categories
                    with dpg.tree_node(label="IC Packages", default_open=True):
                        dpg.add_button(label="BGA", callback=lambda: self.add_component_node("BGA"))
                        dpg.add_button(label="QFP", callback=lambda: self.add_component_node("QFP"))
                        dpg.add_button(label="SOIC", callback=lambda: self.add_component_node("SOIC"))

                    with dpg.tree_node(label="Passives"):
                        dpg.add_button(label="MLCC", callback=lambda: self.add_component_node("MLCC"))
                        dpg.add_button(label="Resistor", callback=lambda: self.add_component_node("Resistor"))

                    with dpg.tree_node(label="Connectors"):
                        dpg.add_button(label="Pin Header", callback=lambda: self.add_component_node("PinHeader"))
                        dpg.add_button(label="USB", callback=lambda: self.add_component_node("USB"))

                # Center panel - Node editor
                with dpg.child_window(tag="editor_panel"):
                    self.node_editor = NodeEditor()
                    self.node_editor.create()

                # Right panel - Properties and preview
                with dpg.child_window(width=300, tag="properties_panel"):
                    dpg.add_text("Properties", color=(255, 255, 0))
                    dpg.add_separator()

                    with dpg.collapsing_header(label="Node Properties", default_open=True):
                        dpg.add_text("Select a node to view properties")

                    with dpg.collapsing_header(label="3D Preview", default_open=True):
                        dpg.add_text("3D preview will appear here")
                        # TODO: Add 3D viewport in Phase 94-95

                    with dpg.collapsing_header(label="Export Settings"):
                        dpg.add_combo(
                            label="Format",
                            items=["STEP", "STL", "IGES", "GLB"],
                            default_value="STEP",
                            tag="export_format",
                        )
                        dpg.add_slider_float(
                            label="STL Resolution",
                            default_value=0.1,
                            min_value=0.01,
                            max_value=1.0,
                            tag="stl_resolution",
                        )

            # Status bar
            with dpg.child_window(height=30, tag="status_bar"):
                dpg.add_text("Ready", tag="status_text")

    # Menu callbacks
    def on_new(self) -> None:
        """Create new project."""
        if self.node_editor:
            self.node_editor.clear()
        self.current_file = None
        self.update_status("New project created")

    def on_open(self) -> None:
        """Open project file."""
        self.update_status("Open project - not yet implemented")

    def on_save(self) -> None:
        """Save current project."""
        if self.current_file:
            self.update_status(f"Saved to {self.current_file}")
        else:
            self.on_save_as()

    def on_save_as(self) -> None:
        """Save project as new file."""
        self.update_status("Save As - not yet implemented")

    def on_export_step(self) -> None:
        """Export to STEP format."""
        self.update_status("Export STEP - not yet implemented")

    def on_export_stl(self) -> None:
        """Export to STL format."""
        self.update_status("Export STL - not yet implemented")

    def on_exit(self) -> None:
        """Exit application."""
        dpg.stop_dearpygui()

    def on_undo(self) -> None:
        """Undo last action."""
        self.update_status("Undo - not yet implemented")

    def on_redo(self) -> None:
        """Redo last undone action."""
        self.update_status("Redo - not yet implemented")

    def on_delete(self) -> None:
        """Delete selected nodes."""
        if self.node_editor:
            self.node_editor.delete_selected()

    def on_reset_zoom(self) -> None:
        """Reset node editor zoom."""
        self.update_status("Reset zoom - not yet implemented")

    def on_fit_window(self) -> None:
        """Fit content to window."""
        self.update_status("Fit to window - not yet implemented")

    def on_toggle_grid(self) -> None:
        """Toggle grid display."""
        self.update_status("Toggle grid - not yet implemented")

    def on_toggle_theme(self) -> None:
        """Toggle between dark and light theme."""
        self.update_status("Toggle theme - not yet implemented")

    def on_show_docs(self) -> None:
        """Show documentation."""
        self.update_status("Opening documentation...")

    def on_show_about(self) -> None:
        """Show about dialog."""
        with dpg.window(label="About KooCAD", modal=True, width=400, height=300):
            dpg.add_text("KooCAD - Parametric Electronic Component CAD")
            dpg.add_separator()
            dpg.add_text("Version: 0.1.0")
            dpg.add_text("A parametric CAD system for electronic components")
            dpg.add_separator()
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(dpg.last_item()))

    def add_component_node(self, component_type: str) -> None:
        """Add component node to editor.

        Args:
            component_type: Type of component to add.
        """
        if self.node_editor:
            self.node_editor.add_component_node(component_type)
            self.update_status(f"Added {component_type} node")

    def update_status(self, message: str) -> None:
        """Update status bar message.

        Args:
            message: Status message to display.
        """
        if dpg.does_item_exist("status_text"):
            dpg.set_value("status_text", message)

    def run(self) -> None:
        """Run the application."""
        # Setup theme
        setup_theme()

        # Setup fonts (if font files available)
        # self.setup_fonts()

        # Create UI
        self.create_ui()

        # Setup viewport
        dpg.create_viewport(title=self.title, width=1600, height=900)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("primary_window", True)

        # Main loop
        dpg.start_dearpygui()
        dpg.destroy_context()


def main() -> None:
    """Main entry point for UI application."""
    app = KooCADApp()
    app.run()


if __name__ == "__main__":
    main()
