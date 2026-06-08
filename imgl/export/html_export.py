"""HTML export for Scene models."""

from __future__ import annotations

from pathlib import Path

from imgl.export._escape import escape_html
from imgl.types import BBox, Element, Scene, Window

_ELEMENT_TAGS = {
    "button": "button",
    "icon_button": "button",
    "input": "input",
    "label": "label",
    "text": "span",
    "toolbar": "nav",
    "unknown": "div",
}


def scene_to_html(
    scene: Scene,
    *,
    embed_image: bool = False,
    title: str | None = None,
) -> str:
    """Render a Scene as an absolutely positioned HTML document."""
    page_title = title or _default_title(scene)
    background = _background_layer(scene, embed_image=embed_image)
    windows_html = "\n".join(_render_window(window) for window in scene.windows)
    orphans_html = "\n".join(
        _render_element(element, parent_offset=BBox(x=0, y=0, w=0, h=0))
        for element in scene.orphan_elements
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape_html(page_title)}</title>
  <style>
{_base_css()}
  </style>
</head>
<body>
  <div class="scene" data-width="{scene.width}" data-height="{scene.height}" style="width:{scene.width}px;height:{scene.height}px">
{background}{windows_html}
{orphans_html}
  </div>
</body>
</html>
"""


def _default_title(scene: Scene) -> str:
    for window in scene.windows:
        if window.title:
            return window.title
    if scene.source_image:
        return Path(scene.source_image).name
    return "imgl scene"


def _background_layer(scene: Scene, *, embed_image: bool) -> str:
    if not embed_image or not scene.source_image:
        return ""
    src = escape_html(scene.source_image)
    return (
        f'    <img class="scene-bg" src="{src}" alt="" '
        f'width="{scene.width}" height="{scene.height}" />\n'
    )


def _base_css() -> str:
    return """    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: #1a1a2e; display: flex; justify-content: center; padding: 16px; }
    .scene { position: relative; background: #fff; overflow: hidden; font-family: system-ui, sans-serif; }
    .scene-bg { position: absolute; left: 0; top: 0; width: 100%; height: 100%; z-index: 0; pointer-events: none; }
    .window { position: absolute; border: 2px solid #4a90d9; background: rgba(74, 144, 217, 0.06); z-index: 1; }
    .window-title { position: absolute; left: 4px; top: -22px; font-size: 12px; color: #4a90d9; font-weight: 600; white-space: nowrap; }
    .ui-el { position: absolute; z-index: 2; font-size: 12px; line-height: 1.2; overflow: hidden; }
    .ui-el[data-type="button"], .ui-el[data-type="icon_button"] {
      border: 1px solid #e67e22; background: rgba(230, 126, 34, 0.2); color: #222;
      display: flex; align-items: center; justify-content: center; padding: 2px 4px;
      cursor: pointer;
    }
    .ui-el[data-type="input"] {
      border: 1px solid #27ae60; background: rgba(39, 174, 96, 0.12); color: #222;
      display: flex; align-items: center; padding: 2px 4px;
    }
    .ui-el[data-type="label"] { color: #2c3e50; background: transparent; font-weight: 500; }
    .ui-el[data-type="text"] { color: #333; background: rgba(255, 255, 0, 0.15); }
    .ui-el[data-type="toolbar"] { border: 1px dashed #7f8c8d; background: rgba(127, 140, 141, 0.1); }
    .ui-el[data-type="unknown"] { border: 1px dashed #95a5a6; background: rgba(149, 165, 166, 0.1); }"""


def _render_window(window: Window) -> str:
    style = _bbox_style(window.bbox)
    title_html = ""
    if window.title:
        title_html = f'      <div class="window-title">{escape_html(window.title)}</div>\n'

    elements_html = "\n".join(
        _render_element(element, parent_offset=window.bbox) for element in window.elements
    )
    return (
        f'    <div class="window" role="window" data-id="{escape_html(window.id)}" '
        f'data-z="{window.z}" style="{style}">\n'
        f"{title_html}{elements_html}"
        f"    </div>\n"
    )


def _render_element(element: Element, *, parent_offset: BBox) -> str:
    tag = _ELEMENT_TAGS.get(element.type, "div")
    local = BBox(
        x=element.bbox.x - parent_offset.x,
        y=element.bbox.y - parent_offset.y,
        w=element.bbox.w,
        h=element.bbox.h,
    )
    style = _bbox_style(local)
    text = element.text or ""
    data_text = f' data-text="{escape_html(text)}"' if text else ""
    label_for = ""
    if element.type == "label" and element.metadata.get("for_input"):
        label_for = f' data-for="{escape_html(str(element.metadata["for_input"]))}"'

    attrs = (
        f'data-id="{escape_html(element.id)}" data-type="{escape_html(element.type)}"'
        f'{data_text}{label_for} style="{style}"'
    )

    if tag == "input":
        value = escape_html(text)
        return (
            f'      <input class="ui-el" type="text" {attrs} value="{value}" '
            f'readonly aria-label="{escape_html(element.metadata.get("label", text or element.id))}" />\n'
        )

    content = escape_html(text)
    if tag == "button":
        return f"      <{tag} class=\"ui-el\" {attrs}>{content}</{tag}>\n"
    return f"      <{tag} class=\"ui-el\" {attrs}>{content}</{tag}>\n"


def _bbox_style(bbox: BBox) -> str:
    return f"left:{bbox.x}px;top:{bbox.y}px;width:{bbox.w}px;height:{bbox.h}px"
