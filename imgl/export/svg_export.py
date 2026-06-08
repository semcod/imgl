"""SVG export for Scene models."""

from __future__ import annotations

from pathlib import Path

from imgl.export._escape import escape_xml
from imgl.types import Element, Scene, Window

_ROLE_COLORS = {
    "window": ("#4a90d9", 0.08),
    "button": ("#e67e22", 0.35),
    "icon_button": ("#e67e22", 0.35),
    "input": ("#27ae60", 0.25),
    "label": ("#2c3e50", 0.0),
    "text": ("#f1c40f", 0.2),
    "toolbar": ("#7f8c8d", 0.15),
    "unknown": ("#95a5a6", 0.12),
}


def scene_to_svg(
    scene: Scene,
    *,
    mode: str = "wireframe",
    background: str | None = None,
) -> str:
    """
    Render a Scene as SVG.

    Modes:
    - wireframe: flat background with element boxes and labels
    - overlay: optional background image with semi-transparent boxes on top
    """
    if mode not in {"wireframe", "overlay"}:
        raise ValueError(f"Unknown SVG mode: {mode}")

    bg_rect = _background_rect(scene, mode=mode, background=background)
    windows_svg = "\n".join(_render_window_svg(window) for window in scene.windows)
    orphans_svg = "\n".join(_render_element_svg(element) for element in scene.orphan_elements)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{scene.width}" height="{scene.height}"
     viewBox="0 0 {scene.width} {scene.height}">
  <title>{escape_xml(_default_title(scene))}</title>
  <style>
{_svg_css()}
  </style>
{bg_rect}{windows_svg}
{orphans_svg}
</svg>
"""


def _default_title(scene: Scene) -> str:
    for window in scene.windows:
        if window.title:
            return window.title
    if scene.source_image:
        return Path(scene.source_image).name
    return "imgl scene"


def _background_rect(scene: Scene, *, mode: str, background: str | None) -> str:
    if mode == "overlay" and background:
        href = escape_xml(background)
        return (
            f'  <image href="{href}" x="0" y="0" '
            f'width="{scene.width}" height="{scene.height}" preserveAspectRatio="none" />\n'
        )
    fill = "#f8f9fa" if mode == "wireframe" else "#ffffff"
    return f'  <rect class="scene-bg" x="0" y="0" width="{scene.width}" height="{scene.height}" fill="{fill}" />\n'


def _svg_css() -> str:
    return """    .window { fill: rgba(74,144,217,0.08); stroke: #4a90d9; stroke-width: 2; }
    .ui-el { stroke-width: 1.5; }
    .ui-button { fill: rgba(230,126,34,0.35); stroke: #e67e22; }
    .ui-input { fill: rgba(39,174,96,0.25); stroke: #27ae60; }
    .ui-label { fill: none; stroke: none; }
    .ui-text { fill: rgba(241,196,15,0.2); stroke: #f1c40f; }
    .ui-toolbar { fill: rgba(127,140,141,0.15); stroke: #7f8c8d; stroke-dasharray: 4 2; }
    .ui-unknown { fill: rgba(149,165,166,0.12); stroke: #95a5a6; stroke-dasharray: 3 2; }
    .label-text { font-family: system-ui, sans-serif; font-size: 11px; fill: #222; }"""


def _render_window_svg(window: Window) -> str:
    bbox = window.bbox
    title_label = ""
    if window.title:
        title_label = (
            f'  <text class="label-text" x="{bbox.x + 4}" y="{max(12, bbox.y - 6)}" '
            f'font-weight="bold" fill="#4a90d9">{escape_xml(window.title)}</text>\n'
        )
    elements_svg = "\n".join(_render_element_svg(element) for element in window.elements)
    return (
        f'  <rect class="window" data-id="{escape_xml(window.id)}" data-z="{window.z}" '
        f'x="{bbox.x}" y="{bbox.y}" width="{bbox.w}" height="{bbox.h}" />\n'
        f"{title_label}{elements_svg}"
    )


def _render_element_svg(element: Element) -> str:
    bbox = element.bbox
    stroke, fill_alpha = _ROLE_COLORS.get(element.type, ("#95a5a6", 0.12))
    css_class = _element_css_class(element.type)
    rect = (
        f'  <rect class="ui-el {css_class}" data-id="{escape_xml(element.id)}" '
        f'data-type="{escape_xml(element.type)}" '
        f'x="{bbox.x}" y="{bbox.y}" width="{bbox.w}" height="{bbox.h}" '
        f'fill="{stroke}" fill-opacity="{fill_alpha}" stroke="{stroke}" />\n'
    )
    if not element.text or element.type in {"input"}:
        return rect

    text_x = bbox.x + 4
    text_y = bbox.y + min(bbox.h - 4, 14)
    text_svg = (
        f'  <text class="label-text" data-for="{escape_xml(element.id)}" '
        f'x="{text_x}" y="{text_y}">{escape_xml(element.text)}</text>\n'
    )
    if element.type == "label":
        return text_svg
    return rect + text_svg


def _element_css_class(element_type: str) -> str:
    mapping = {
        "button": "ui-button",
        "icon_button": "ui-button",
        "input": "ui-input",
        "label": "ui-label",
        "text": "ui-text",
        "toolbar": "ui-toolbar",
    }
    return mapping.get(element_type, "ui-unknown")
