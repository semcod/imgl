"""Flat actuation layers (bbox + click_center) for vdisplay/koru mouse control."""

from __future__ import annotations

from typing import Any


def bbox_center(bbox: dict[str, Any] | None) -> dict[str, int] | None:
    if not isinstance(bbox, dict):
        return None
    x = int(bbox.get("x") or 0)
    y = int(bbox.get("y") or 0)
    w = int(bbox.get("w") or bbox.get("width") or 0)
    h = int(bbox.get("h") or bbox.get("height") or 0)
    if w <= 0 or h <= 0:
        return None
    return {"x": x + w // 2, "y": y + h // 2}


def bbox_area(bbox: dict[str, Any] | None) -> int:
    if not isinstance(bbox, dict):
        return 0
    w = int(bbox.get("w") or bbox.get("width") or 0)
    h = int(bbox.get("h") or bbox.get("height") or 0)
    return max(0, w * h)


def layer_from_bbox(
    *,
    kind: str,
    layer_id: str | None = None,
    text: str | None = None,
    bbox: dict[str, Any] | None = None,
    confidence: float | None = None,
) -> dict[str, Any] | None:
    if not isinstance(bbox, dict):
        return None
    center = bbox_center(bbox)
    if center is None:
        return None
    layer: dict[str, Any] = {
        "kind": kind,
        "id": layer_id,
        "text": text,
        "bbox": bbox,
        "center": center,
        "click_center": center,
    }
    if confidence is not None:
        layer["confidence"] = confidence
    return layer


def _element_layer_from_dict(element: dict[str, Any]) -> dict[str, Any] | None:
    return layer_from_bbox(
        kind=str(element.get("type") or element.get("role") or "element"),
        layer_id=str(element.get("id") or ""),
        text=element.get("text"),
        bbox=element.get("bbox"),
        confidence=float(element.get("confidence") or 0.0) or None,
    )


def _window_layers(windows: list) -> list[dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    for window in windows:
        if not isinstance(window, dict):
            continue
        wl = layer_from_bbox(
            kind="window",
            layer_id=str(window.get("id") or ""),
            text=window.get("title"),
            bbox=window.get("bbox"),
        )
        if wl:
            layers.append(wl)
        for element in window.get("elements") or []:
            if isinstance(element, dict):
                item = _element_layer_from_dict(element)
                if item:
                    layers.append(item)
    return layers


def scene_to_actuation_layers(scene: dict[str, Any], *, limit: int = 128) -> list[dict[str, Any]]:
    """Flatten IMGL scene JSON to click-ready layers for autonomy (vdisplay VQL sidecar)."""
    if not isinstance(scene, dict):
        return []
    layers = _window_layers(scene.get("windows") or [])

    for element in scene.get("elements") or []:
        if isinstance(element, dict):
            item = _element_layer_from_dict(element)
            if item:
                layers.append(item)

    for ocr in scene.get("ocr_boxes") or []:
        if not isinstance(ocr, dict):
            continue
        text = str(ocr.get("text") or "").strip()
        if not text:
            continue
        item = layer_from_bbox(
            kind="ocr",
            text=text,
            bbox=ocr.get("bbox"),
            confidence=float(ocr.get("confidence") or 0.0) or None,
        )
        if item:
            layers.append(item)

    return layers[:limit]


def imgl_result_to_actuation_layers(imgl: dict[str, Any], *, limit: int = 128) -> list[dict[str, Any]]:
    """Extract actuation layers from vdisplay-style ``ctx.imgl`` block."""
    if not imgl.get("ok"):
        return []
    scene = imgl.get("scene")
    if not isinstance(scene, dict):
        return []
    return scene_to_actuation_layers(scene, limit=limit)
