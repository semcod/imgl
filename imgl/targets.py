"""Resolve chat/editor click targets from flat actuation layers (photo VQL)."""

from __future__ import annotations

import re
from typing import Any

from imgl.export.actuation_layers import bbox_area, bbox_center


def _has_chat_token(text: str) -> bool:
    return bool(re.search(r"\b(chat|composer|aichat|copilot)\b", text.lower()))


def _bbox_center_x(bounds: dict[str, Any] | None) -> float:
    if not isinstance(bounds, dict):
        return 0.0
    x = float(bounds.get("x") or 0)
    w = float(bounds.get("w") or bounds.get("width") or 0)
    return x + (w / 2.0)


def _bbox_center_y(bounds: dict[str, Any] | None) -> float:
    if not isinstance(bounds, dict):
        return 0.0
    y = float(bounds.get("y") or 0)
    h = float(bounds.get("h") or bounds.get("height") or 0)
    return y + (h / 2.0)


def normalize_actuation_element(layer: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize vdisplay sidecar layer or koru ui_element to a common actuation shape."""
    if not isinstance(layer, dict):
        return None
    bounds = layer.get("bounds") or layer.get("bbox") or {}
    if not isinstance(bounds, dict):
        bounds = {}
    role = layer.get("role") or layer.get("kind") or "element"
    cc = layer.get("click_center") or layer.get("center")
    if not cc and bounds:
        cc = bbox_center(bounds)
    if not cc:
        return None
    return {
        "id": layer.get("id"),
        "role": role,
        "label": layer.get("label") or layer.get("text"),
        "bounds": bounds,
        "click_center": cc,
        "metadata": layer.get("metadata") or {
            k: layer[k] for k in ("confidence", "location") if k in layer
        },
        "location": layer.get("location"),
    }


def normalize_actuation_elements(layers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for layer in layers:
        norm = normalize_actuation_element(layer)
        if norm:
            out.append(norm)
    return out


def _target_result(
    element: dict[str, Any],
    *,
    note: str,
    source: str | None,
) -> dict[str, Any]:
    return {
        "click_center": element.get("click_center") or {},
        "id": element.get("id"),
        "role": element.get("role"),
        "bounds": element.get("bounds"),
        "note": note,
        "source": source or "imgl-targets",
    }


def resolve_chat_target(
    layers: list[dict[str, Any]],
    *,
    source: str | None = None,
    fallback_center: tuple[int, int] = (1024, 640),
) -> dict[str, Any]:
    """Locate chat/composer panel from photo VQL actuation layers (IDE-agnostic)."""
    els = normalize_actuation_elements(layers)

    ask_cands: list[tuple[dict[str, Any], float]] = []
    for t in els:
        label = str(t.get("label") or "").lower()
        cc = t.get("click_center") or {}
        if not cc:
            continue
        cy = float(cc.get("y") or 0)
        if "ask anything" in label or ("ask" in label and "anything" in label):
            ask_cands.append((t, 3000.0 - cy))
        elif re.search(r"\bask\b", label) and cy <= 350:
            ask_cands.append((t, 2000.0 - cy))
    if ask_cands:
        ask_cands.sort(key=lambda item: -item[1])
        t, _ = ask_cands[0]
        return _target_result(
            t,
            note=f"top chat placeholder from photo VQL ({source})",
            source=source,
        )

    for t in els:
        ident = str(t.get("id") or "").lower()
        if _has_chat_token(ident):
            cc = t.get("click_center") or {}
            if cc:
                return _target_result(
                    t,
                    note=f"explicit chat/composer token from photo VQL ({source})",
                    source=source,
                )

    panel_cands: list[tuple[dict[str, Any], dict[str, Any], float]] = []
    for t in els:
        if t.get("role") != "panel":
            continue
        b = t.get("bounds") or {}
        cx = _bbox_center_x(b)
        area = bbox_area(b)
        loc = str((t.get("metadata") or {}).get("location") or t.get("location") or "").lower()
        cc = t.get("click_center")
        if cc and area > 10000:
            score = (3 if "center" in loc else 0) + (2 if cx > 800 else 0) + (area / 100000.0)
            panel_cands.append((t, cc, score))
    if panel_cands:
        panel_cands.sort(key=lambda p: -p[2])
        t, _, _ = panel_cands[0]
        return _target_result(
            t,
            note=f"panel candidate from photo VQL (center/right priority for chat; {source})",
            source=source,
        )

    input_cands: list[tuple[dict[str, Any], float]] = []
    for t in els:
        if t.get("role") != "input":
            continue
        b = t.get("bounds") or {}
        cx = _bbox_center_x(b)
        cy = _bbox_center_y(b)
        area = bbox_area(b)
        if not t.get("click_center"):
            continue
        cy = _bbox_center_y(b)
        if area < 2000 and cy < 900:
            continue
        score = (2 if cx > 850 else 0) + (3 if cx > 1200 else 0) + (2 if cy > 700 else 0) + (4 if cy > 950 else 0)
        input_cands.append((t, score))
    if input_cands:
        input_cands.sort(key=lambda p: (-p[1], -bbox_area(p[0].get("bounds"))))
        t, _ = input_cands[0]
        return _target_result(
            t,
            note=f"composer input from photo VQL (right/bottom priority; {source})",
            source=source,
        )

    for t in els:
        if str(t.get("id", "")) == "window_0" and t.get("role") == "window":
            cc = t.get("click_center")
            if cc:
                return _target_result(
                    t,
                    note="main window from screen photo VQL for chat/editor focus",
                    source=source,
                )

    for t in els:
        if t.get("role") == "canvas":
            cc = t.get("click_center")
            if cc:
                return _target_result(
                    t,
                    note="canvas from screen photo VQL for chat/editor focus",
                    source=source,
                )

    fx, fy = fallback_center
    return {
        "click_center": {"x": fx, "y": fy, "note": "fallback editor/chat area center from photo VQL analysis"},
        "id": "photo-chat-editor-center",
        "role": "editor-chat-area",
        "note": "hardened fallback center for current foto screen",
        "source": source or "imgl-targets-fallback",
    }


def resolve_editor_target(
    layers: list[dict[str, Any]],
    *,
    source: str | None = None,
    fallback_center: tuple[int, int] = (1024, 640),
) -> dict[str, Any]:
    """Locate main editor window/area from photo VQL actuation layers."""
    els = normalize_actuation_elements(layers)

    for t in els:
        if str(t.get("id", "")) == "window_0" and t.get("role") == "window":
            cc = t.get("click_center")
            if cc:
                return _target_result(
                    t,
                    note=f"main editor window from photo VQL ({source})",
                    source=source,
                )

    editor_cands: list[tuple[dict[str, Any], float]] = []
    for t in els:
        role = t.get("role")
        if role not in ("window", "panel", "canvas"):
            continue
        area = bbox_area(t.get("bounds"))
        loc = str((t.get("metadata") or {}).get("location") or t.get("location") or "").lower()
        cc = t.get("click_center")
        tid = str(t.get("id", "")).lower()
        if cc and area > 50000:
            score = area / 100000.0
            if "center" in loc:
                score += 100
            if "window" in tid or "dp1" in tid or "editor" in tid:
                score += 200
            editor_cands.append((t, score))
    if editor_cands:
        editor_cands.sort(key=lambda p: -p[1])
        t, _ = editor_cands[0]
        return _target_result(
            t,
            note=f"main editor area from photo VQL (largest/center window or panel; {source})",
            source=source,
        )

    fx, fy = fallback_center
    return {
        "click_center": {"x": fx, "y": fy, "note": "fallback main editor area center from photo VQL analysis"},
        "id": "photo-editor-center",
        "role": "editor",
        "note": "hardened fallback editor center for current foto (for precise edit via coords)",
        "source": source or "imgl-targets-fallback",
    }


def resolve_actuation_target(
    layers: list[dict[str, Any]],
    *,
    role: str = "chat",
    source: str | None = None,
    fallback_center: tuple[int, int] = (1024, 640),
) -> dict[str, Any]:
    """Unified entry: ``role`` is ``chat`` or ``editor``."""
    if role == "editor":
        return resolve_editor_target(layers, source=source, fallback_center=fallback_center)
    return resolve_chat_target(layers, source=source, fallback_center=fallback_center)
