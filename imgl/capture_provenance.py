"""Capture provenance sidecar and scene enrichment from vdisplay metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from imgl.types import Scene

_VISION_IOU_MIN = 0.3


def capture_meta_path(image: str | Path) -> Path:
    return Path(image).with_suffix(".capture.json")


def save_capture_meta(image: str | Path, meta: dict[str, Any]) -> Path:
    """Persist capture backend metadata next to the PNG."""
    image_path = Path(image).expanduser()
    payload = {"path": str(image_path.resolve()), **meta}
    out = capture_meta_path(image_path)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def load_capture_meta(image: str | Path) -> dict[str, Any]:
    path = capture_meta_path(image)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def enrich_scene_provenance(scene: Scene) -> Scene:
    """Attach capture sidecar and optional vdisplay OS window correlation."""
    if not scene.source_image:
        return scene

    metadata = dict(scene.metadata)
    capture = load_capture_meta(scene.source_image)
    if capture:
        metadata["capture"] = capture

    window_os = _correlate_os_windows(scene)
    if window_os:
        metadata["window_os"] = window_os

    return Scene(
        width=scene.width,
        height=scene.height,
        source_image=scene.source_image,
        windows=scene.windows,
        orphan_elements=scene.orphan_elements,
        ocr_boxes=scene.ocr_boxes,
        metadata=metadata,
    )


def _correlate_os_windows(scene: Scene) -> dict[str, dict[str, Any]]:
    try:
        from imgl.vdisplay_bridge import (
            correlate_windows,
            list_os_windows,
            vdisplay_available,
        )
    except ImportError:
        return {}

    if not vdisplay_available() or not scene.windows:
        return {}

    vision = [
        {
            "id": window.id,
            "title": window.title or window.id,
            "bbox": window.bbox.to_dict(),
            "source": "imgl_vision",
        }
        for window in scene.windows
    ]
    rows = correlate_windows(
        list_os_windows(),
        vision,
        screen_width=scene.width,
        screen_height=scene.height,
    )

    window_os: dict[str, dict[str, Any]] = {}
    for row in rows:
        match = row.get("vision_match")
        if not match:
            continue
        if float(row.get("vision_iou") or 0) < _VISION_IOU_MIN:
            continue
        window_os[str(match["id"])] = {
            "app_label": row.get("app_label"),
            "window_id": row.get("window_id"),
            "monitor_name": row.get("monitor_name"),
            "vision_iou": row.get("vision_iou"),
            "nl": row.get("nl"),
        }
    return window_os


__all__ = [
    "capture_meta_path",
    "enrich_scene_provenance",
    "load_capture_meta",
    "save_capture_meta",
]
