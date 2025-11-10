"""
Theme and styling for DearPyGui UI.

This module provides dark and light themes for the application.
"""

from __future__ import annotations

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    dpg = None  # type: ignore


def setup_theme(dark: bool = True) -> None:
    """Setup application theme.

    Args:
        dark: If True, use dark theme. Otherwise use light theme.
    """
    if dpg is None:
        return

    if dark:
        setup_dark_theme()
    else:
        setup_light_theme()


def setup_dark_theme() -> None:
    """Setup dark theme (default)."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Window colors
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (25, 25, 25, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 30, 30, 255))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (35, 35, 35, 255))

            # Frame colors
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (45, 45, 45, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (55, 55, 55, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (65, 65, 65, 255))

            # Title bar
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (20, 20, 20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (30, 30, 30, 255))

            # Button colors
            dpg.add_theme_color(dpg.mvThemeCol_Button, (70, 70, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (90, 90, 90, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (110, 110, 110, 255))

            # Header colors
            dpg.add_theme_color(dpg.mvThemeCol_Header, (60, 60, 60, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (80, 80, 80, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (100, 100, 100, 255))

            # Text colors
            dpg.add_theme_color(dpg.mvThemeCol_Text, (220, 220, 220, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (128, 128, 128, 255))

            # Slider colors
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (100, 150, 200, 255))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (120, 170, 220, 255))

            # Scrollbar
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (35, 35, 35, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (70, 70, 70, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (90, 90, 90, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (110, 110, 110, 255))

            # Separator
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (80, 80, 80, 255))

            # Menu bar
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (30, 30, 30, 255))

            # Border
            dpg.add_theme_color(dpg.mvThemeCol_Border, (60, 60, 60, 255))

            # Node editor specific
            dpg.add_theme_color(dpg.mvNodeCol_GridBackground, (25, 25, 25, 255))
            dpg.add_theme_color(dpg.mvNodeCol_GridLine, (50, 50, 50, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, (40, 40, 40, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundHovered, (50, 50, 50, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackgroundSelected, (60, 60, 60, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, (80, 80, 80, 255))
            dpg.add_theme_color(dpg.mvNodeCol_TitleBar, (50, 50, 50, 255))
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarHovered, (60, 60, 60, 255))
            dpg.add_theme_color(dpg.mvNodeCol_TitleBarSelected, (70, 70, 70, 255))
            dpg.add_theme_color(dpg.mvNodeCol_Link, (100, 150, 200, 255))
            dpg.add_theme_color(dpg.mvNodeCol_LinkHovered, (120, 170, 220, 255))
            dpg.add_theme_color(dpg.mvNodeCol_LinkSelected, (140, 190, 240, 255))
            dpg.add_theme_color(dpg.mvNodeCol_Pin, (200, 200, 200, 255))
            dpg.add_theme_color(dpg.mvNodeCol_PinHovered, (220, 220, 220, 255))

            # Style
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 4, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 14)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 3)

    dpg.bind_theme(global_theme)


def setup_light_theme() -> None:
    """Setup light theme."""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Window colors
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (240, 240, 240, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (245, 245, 245, 255))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (250, 250, 250, 255))

            # Frame colors
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (230, 230, 230, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (220, 220, 220, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (210, 210, 210, 255))

            # Title bar
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (220, 220, 220, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (200, 200, 200, 255))

            # Button colors
            dpg.add_theme_color(dpg.mvThemeCol_Button, (180, 180, 180, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (160, 160, 160, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (140, 140, 140, 255))

            # Text colors
            dpg.add_theme_color(dpg.mvThemeCol_Text, (20, 20, 20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (128, 128, 128, 255))

            # Slider colors
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (80, 130, 180, 255))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (60, 110, 160, 255))

            # Node editor
            dpg.add_theme_color(dpg.mvNodeCol_GridBackground, (245, 245, 245, 255))
            dpg.add_theme_color(dpg.mvNodeCol_GridLine, (220, 220, 220, 255))
            dpg.add_theme_color(dpg.mvNodeCol_NodeBackground, (255, 255, 255, 255))
            dpg.add_theme_color(dpg.mvNodeCol_Link, (80, 130, 180, 255))

            # Style
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)

    dpg.bind_theme(global_theme)
