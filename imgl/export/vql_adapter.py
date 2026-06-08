"""VQL program export for Scene models."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from imgl.types import BBox, Element, OcrBox, Scene, Window

VQL_VERSION = "1.0"

_ROLE_STYLES: dict[str, dict[str, Any]] = {
    "window": {"color": "#4A90D9", "fill": False, "stroke_width": 2.0, "opacity": 0.9},
    "panel": {"color": "#7B68EE", "fill": False, "stroke_width": 1.5, "opacity": 0.85},
    "titlebar": {"color": "#FFD700", "fill": True, "stroke_width": 1.0, "opacity": 0.35},
    "toolbar": {"color": "#20B2AA", "fill": False, "stroke_width": 1.5, "opacity": 0.8},
    "button": {"color": "#FF6B6B", "fill": True, "stroke_width": 1.0, "opacity": 0.55},
    "icon_button": {"color": "#FFA500", "fill": True, "stroke_width": 1.0, "opacity": 0.6},
    "input": {"color": "#27AE60", "fill": True, "stroke_width": 1.0, "opacity": 0.45},
    "label": {"color": "#2C3E50", "fill": False, "stroke_width": 1.0, "opacity": 0.7},
    "text": {"color": "#F1C40F", "fill": True, "stroke_width": 1.0, "opacity": 0.25},
    "unknown": {"color": "#888888", "fill": False, "stroke_width": 1.0, "opacity": 0.5},
}


def scene_to_vql(
    scene: Scene,
    *,
    include_grid: bool = False,
    grid: int = 12,
) -> dict[str, Any]:
    """Convert a Scene to a VQLProgram-compatible dict."""
    layers: list[dict[str, Any]] = []

    if include_grid and scene.source_image and Path(scene.source_image).is_file():
        grid_layer = _grid_layer(scene.source_image, grid=grid)
        if grid_layer:
            layers.append(grid_layer)

    window_objects = [_window_to_object(window, scene.width, scene.height) for window in scene.windows]
    if window_objects:
        layers.append({"id": "windows", "objects": window_objects, "visible": True})

    ui_objects: list[dict[str, Any]] = []
    for window in scene.windows:
        for element in window.elements:
            ui_objects.append(_element_to_object(element, scene.width, scene.height))
    for element in scene.orphan_elements:
        ui_objects.append(_element_to_object(element, scene.width, scene.height))

    if ui_objects:
        layers.append({"id": "ui_elements", "objects": ui_objects, "visible": True})

    text_objects = [_ocr_to_object(box, scene.width, scene.height) for box in scene.ocr_boxes]
    if text_objects:
        layers.append({"id": "text_regions", "objects": text_objects, "visible": True})

    image_url = ""
    if scene.source_image and Path(scene.source_image).is_file():
        image_url = f"file://{Path(scene.source_image).resolve()}"

    roles = dict(scene.metadata.get("roles", {}))
    return {
        "version": VQL_VERSION,
        "render_target": "svg",
        "scene": {
            "width": float(scene.width),
            "height": float(scene.height),
            "background": "#FFFFFF",
            "url": image_url,
            "app": "desktop",
            "layers": layers,
            "relations": [],
        },
        "validation": None,
        "metadata": {
            "source": "imgl",
            "image": scene.source_image or "",
            "element_count": len(ui_objects),
            "by_role": roles,
            "detect_source": scene.metadata.get("detect_source", ""),
            "ocr_backend": scene.metadata.get("ocr_backend", ""),
            "lang": scene.metadata.get("lang", ""),
            "analyzed_at": datetime.now(UTC).isoformat(),
        },
    }


def scene_to_vql_json(
    scene: Scene,
    *,
    include_grid: bool = False,
    grid: int = 12,
    indent: int = 2,
) -> str:
    """Serialize Scene as VQL JSON string."""
    return json.dumps(
        scene_to_vql(scene, include_grid=include_grid, grid=grid),
        indent=indent,
        ensure_ascii=False,
    )


def write_vql_program(
    scene: Scene,
    path: str | Path,
    *,
    include_grid: bool = False,
    grid: int = 12,
) -> Path:
    """Write a VQL program JSON file from a Scene."""
    out = Path(path)
    out.write_text(
        scene_to_vql_json(scene, include_grid=include_grid, grid=grid),
        encoding="utf-8",
    )
    return out


def _grid_layer(image_path: str, *, grid: int) -> dict[str, Any] | None:
    try:
        from vql.adopt.window import screenshot_to_program
    except ImportError:
        return None

    program = screenshot_to_program(image_path, grid=grid)
    for layer in program.scene.layers:
        if layer.id == "screen_regions":
            return layer.to_dict()
    return None


def _bbox_norm(bbox: BBox, width: int, height: int) -> list[float]:
    x0, y0, x1, y1 = bbox.as_xyxy()
    return [
        round(x0 / width, 4) if width else 0.0,
        round(y0 / height, 4) if height else 0.0,
        round(x1 / width, 4) if width else 0.0,
        round(y1 / height, 4) if height else 0.0,
    ]


def _location_label(cx: float, cy: float, width: int, height: int) -> str:
    nx, ny = cx / max(1, width), cy / max(1, height)
    vert = "top" if ny < 0.33 else "bottom" if ny > 0.66 else "middle"
    horiz = "left" if nx < 0.33 else "right" if nx > 0.66 else "center"
    if vert == "middle" and horiz == "center":
        return "center"
    if horiz == "center":
        return vert
    if vert == "middle":
        return horiz
    return f"{vert}-{horiz}"


def _object_from_bbox(
    *,
    obj_id: str,
    role: str,
    bbox: BBox,
    width: int,
    height: int,
    label: str = "",
    confidence: float = 0.5,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    x0, y0, x1, y1 = bbox.as_xyxy()
    bw, bh = max(1.0, float(x1 - x0)), max(1.0, float(y1 - y0))
    cx, cy = x0 + bw / 2, y0 + bh / 2
    metadata = {
        "role": role,
        "label": label,
        "location": _location_label(cx, cy, width, height),
        "bbox": [x0, y0, x1, y1],
        "bbox_norm": _bbox_norm(bbox, width, height),
        "confidence": round(confidence, 3),
        "source": "imgl",
    }
    if extra_metadata:
        metadata.update(extra_metadata)

    return {
        "id": obj_id,
        "primitives": [{"shape_type": "rectangle", "params": {"width": bw, "height": bh}}],
        "style": dict(_ROLE_STYLES.get(role, _ROLE_STYLES["unknown"])),
        "transform": {
            "translate_x": 0.0,
            "translate_y": 0.0,
            "scale_x": 1.0,
            "scale_y": 1.0,
            "rotate_deg": 0.0,
        },
        "center_x": cx,
        "center_y": cy,
        "anchors": [],
        "constraints": [],
        "metadata": metadata,
    }


def _window_to_object(window: Window, width: int, height: int) -> dict[str, Any]:
    return _object_from_bbox(
        obj_id=window.id,
        role="window",
        bbox=window.bbox,
        width=width,
        height=height,
        label=window.title or window.id,
        confidence=0.8,
        extra_metadata={"z": window.z, "title": window.title},
    )


def _element_to_object(element: Element, width: int, height: int) -> dict[str, Any]:
    role = element.type if element.type in _ROLE_STYLES else "unknown"
    return _object_from_bbox(
        obj_id=element.id,
        role=role,
        bbox=element.bbox,
        width=width,
        height=height,
        label=element.text or element.metadata.get("label", "") or role,
        confidence=element.confidence,
        extra_metadata={
            "text": element.text,
            "element_type": element.type,
            **element.metadata,
        },
    )


def _ocr_to_object(box: OcrBox, width: int, height: int) -> dict[str, Any]:
    return _object_from_bbox(
        obj_id=f"ocr-{box.text[:20].replace(' ', '_')}-{box.bbox.x}-{box.bbox.y}",
        role="text",
        bbox=box.bbox,
        width=width,
        height=height,
        label=box.text,
        confidence=box.confidence / 100.0 if box.confidence > 1 else box.confidence,
        extra_metadata={"ocr_level": box.level, "source": "imgl_ocr"},
    )
