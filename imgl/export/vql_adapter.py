"""VQL program export for Scene models."""

from __future__ import annotations

import json
import os
import sys
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


def _scene_element_objects(scene: Scene) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    for window in scene.windows:
        for element in window.elements:
            objects.append(_element_to_object(element, scene.width, scene.height))
    for element in scene.orphan_elements:
        objects.append(_element_to_object(element, scene.width, scene.height))
    return objects


def scene_to_vql(
    scene: Scene,
    *,
    include_grid: bool = False,
    grid: int = 12,
) -> dict[str, Any]:
    """Convert a Scene to a VQLProgram-compatible dict."""
    layers: list[dict[str, Any]] = []
    window_os = dict(scene.metadata.get("window_os", {}))

    if include_grid and scene.source_image and Path(scene.source_image).is_file():
        grid_layer = _grid_layer(scene.source_image, grid=grid)
        if grid_layer:
            layers.append(grid_layer)

    window_objects = [
        _window_to_object(window, scene.width, scene.height, os_meta=window_os.get(window.id))
        for window in scene.windows
    ]
    if window_objects:
        layers.append({"id": "windows", "objects": window_objects, "visible": True})

    ui_objects = _scene_element_objects(scene)
    if ui_objects:
        layers.append({"id": "ui_elements", "objects": ui_objects, "visible": True})

    text_objects = [_ocr_to_object(box, scene.width, scene.height) for box in scene.ocr_boxes]
    if text_objects:
        layers.append({"id": "text_regions", "objects": text_objects, "visible": True})

    all_objects = window_objects + ui_objects + text_objects
    relations = _build_contains_relations(all_objects)

    image_url = ""
    if scene.source_image and Path(scene.source_image).is_file():
        image_url = f"file://{Path(scene.source_image).resolve()}"

    roles = dict(scene.metadata.get("roles", {}))
    metadata: dict[str, Any] = {
        "source": "imgl",
        "image": scene.source_image or "",
        "element_count": len(ui_objects),
        "by_role": roles,
        "detect_source": scene.metadata.get("detect_source", ""),
        "ocr_backend": scene.metadata.get("ocr_backend", ""),
        "lang": scene.metadata.get("lang", ""),
        "analyzed_at": datetime.now(UTC).isoformat(),
    }
    capture = scene.metadata.get("capture")
    if isinstance(capture, dict) and capture:
        metadata["capture"] = capture
    if window_os:
        metadata["window_os"] = window_os

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
            "relations": relations,
        },
        "validation": None,
        "metadata": metadata,
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


def validate_vql_export(program: dict[str, Any]) -> list[str]:
    """Validate exported program with oqlos/vql when installed."""
    try:
        from vql import VQLProgram, validate_program
    except ImportError:
        return []

    issues: list[str] = []
    try:
        model = VQLProgram.from_dict(program)
        issues.extend(model.validate())
        report = validate_program(model)
        if not report.passed:
            issues.extend(str(item) for item in report.issues)
        try:
            from vql import validate_program_metadata

            issues.extend(validate_program_metadata(program.get("metadata")))
        except ImportError:
            pass
    except Exception as exc:
        issues.append(str(exc))
    return issues


def write_vql_program(
    scene: Scene,
    path: str | Path,
    *,
    include_grid: bool = False,
    grid: int = 12,
    validate: bool | None = None,
) -> Path:
    """Write a VQL program JSON file from a Scene."""
    payload = scene_to_vql_json(scene, include_grid=include_grid, grid=grid)
    out = Path(path)
    out.write_text(payload, encoding="utf-8")

    if validate is None:
        validate = os.environ.get("IMGL_VALIDATE_VQL", "1").strip().lower() not in {
            "0",
            "false",
            "no",
            "off",
        }
    if validate:
        program = json.loads(payload)
        issues = validate_vql_export(program)
        if issues:
            print(
                f"VQL validation warnings for {out}:\n  "
                + "\n  ".join(issues[:8]),
                file=sys.stderr,
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


def _build_contains_relations(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Infer contains relations from bbox nesting (window > panel > button)."""
    role_rank = {
        "window": 0,
        "panel": 1,
        "titlebar": 1,
        "toolbar": 2,
        "button": 3,
        "icon_button": 3,
        "input": 3,
        "label": 4,
        "text": 5,
    }
    relations: list[dict[str, Any]] = []
    for parent in objects:
        p_meta = parent.get("metadata", {})
        p_role = p_meta.get("role", "")
        p_bbox = p_meta.get("bbox", [])
        if not p_bbox:
            continue
        for child in objects:
            if parent.get("id") == child.get("id"):
                continue
            c_meta = child.get("metadata", {})
            c_role = c_meta.get("role", "")
            c_bbox = c_meta.get("bbox", [])
            if not c_bbox:
                continue
            if role_rank.get(p_role, 9) >= role_rank.get(c_role, 9):
                continue
            if _bbox_contains(p_bbox, c_bbox):
                relations.append(
                    {
                        "kind": "contains",
                        "source": parent["id"],
                        "target": child["id"],
                        "args": {"parent_role": p_role, "child_role": c_role},
                    }
                )
    return relations


def _bbox_contains(outer: list[float | int], inner: list[float | int]) -> bool:
    ox0, oy0, ox1, oy1 = outer[:4]
    ix0, iy0, ix1, iy1 = inner[:4]
    return ox0 <= ix0 and oy0 <= iy0 and ox1 >= ix1 and oy1 >= iy1


def _window_to_object(
    window: Window,
    width: int,
    height: int,
    *,
    os_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    extra: dict[str, Any] = {"z": window.z, "title": window.title}
    if os_meta:
        extra["os_window_id"] = os_meta.get("window_id")
        extra["app_label"] = os_meta.get("app_label")
        extra["monitor_name"] = os_meta.get("monitor_name")
        if os_meta.get("vision_iou") is not None:
            extra["vision_iou"] = os_meta.get("vision_iou")
    return _object_from_bbox(
        obj_id=window.id,
        role="window",
        bbox=window.bbox,
        width=width,
        height=height,
        label=window.title or window.id,
        confidence=0.8,
        extra_metadata=extra,
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
