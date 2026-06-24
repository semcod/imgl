"""Bridge vdisplay (OS window truth) with imgl (vision layout)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_VDISPLAY_IMPORT_ERROR: str | None = None

try:
    from vdisplay.discovery import diagnose_display as _vdisplay_diagnose_display
    from vdisplay.discovery import list_monitors as _vdisplay_list_monitors
    from vdisplay.discovery import list_windows as _vdisplay_list_windows

    _VDISPLAY_AVAILABLE = True
except ImportError as exc:
    _VDISPLAY_AVAILABLE = False
    _VDISPLAY_IMPORT_ERROR = str(exc)


def vdisplay_available() -> bool:
    return _VDISPLAY_AVAILABLE


def vdisplay_missing_message() -> str:
    if _VDISPLAY_AVAILABLE:
        return ""
    root = os.environ.get("VDISPLAY_ROOT", "~/github/wronai/vdisplay").replace("~", str(Path.home()))
    return (
        f"vdisplay missing ({_VDISPLAY_IMPORT_ERROR}). "
        f"Run: make install-dev  (auto: pip install -e {root}[pillow])"
    )


def default_display() -> str | None:
    raw = os.environ.get("IMGL_DISPLAY", os.environ.get("DISPLAY", "")).strip()
    return raw or None


def list_os_windows(*, apps_only: bool = True, display: str | None = None) -> list[dict[str, Any]]:
    if not _VDISPLAY_AVAILABLE:
        return []
    return list(_vdisplay_list_windows(display=display or default_display(), apps_only=apps_only))


def list_os_monitors(*, display: str | None = None) -> list[dict[str, Any]]:
    if not _VDISPLAY_AVAILABLE:
        return []
    return list(_vdisplay_list_monitors(display=display or default_display()))


def diagnose_os_display(*, display: str | None = None) -> dict[str, Any]:
    if not _VDISPLAY_AVAILABLE:
        return {"ok": False, "available": False, "error": vdisplay_missing_message()}
    try:
        payload = _vdisplay_diagnose_display(display=display or default_display())
        payload["available"] = True
        payload["ok"] = not payload.get("error")
        return payload
    except Exception as exc:
        return {"ok": False, "available": True, "error": str(exc)}


def _norm(value: str) -> str:
    return value.strip().lower()


def find_os_window(
    match: str,
    *,
    apps_only: bool = True,
    display: str | None = None,
) -> dict[str, Any] | None:
    """Match by app_label, title, wm_class, window_id, or nl text."""
    needle = _norm(match)
    if not needle:
        return None
    for window in list_os_windows(apps_only=apps_only, display=display):
        for key in ("app_label", "title", "wm_class", "window_id", "nl"):
            raw = window.get(key)
            if raw and needle in _norm(str(raw)):
                return window
    return None


def suggest_imgl_region(window: dict[str, Any], *, screen_height: int) -> str:
    """Map OS window vertical position to imgl region alias."""
    y = int(window.get("y") or 0)
    h = int(window.get("height") or 0)
    center = y + h // 2
    ratio = center / max(1, screen_height)
    if ratio < 0.34:
        return "region-top"
    if ratio < 0.67:
        return "region-middle"
    return "region-bottom"


def list_vision_windows(image: str | Path) -> list[dict[str, Any]]:
    from imgl.paths import resolve_image_path
    from imgl.scene_cache import load_or_analyze
    from imgl.window_scope import discover_windows, summarize_windows

    image_path = str(resolve_image_path(image))
    vql_file = str(Path(image_path).with_suffix(".vql.json"))
    scene = load_or_analyze(image_path, vql_file=vql_file, refresh=False)
    summaries = summarize_windows(scene, image_path=image_path)
    windows = discover_windows(scene)
    by_id = {item.id: item for item in windows}
    payload: list[dict[str, Any]] = []
    for item in summaries:
        window = by_id.get(item.window.id, item.window)
        payload.append(
            {
                "id": window.id,
                "title": window.title or window.id,
                "bbox": window.bbox.to_dict(),
                "element_count": item.element_count,
                "interactive_count": item.interactive_count,
                "source": "imgl_vision",
            }
        )
    return payload


def _best_vision_match(
    ox: int, oy: int, ow: int, oh: int,
    vision_windows: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, float]:
    best: dict[str, Any] | None = None
    best_iou = 0.0
    for vis in vision_windows:
        bbox = vis.get("bbox") or {}
        vx = int(bbox.get("x") or 0)
        vy = int(bbox.get("y") or 0)
        vw = int(bbox.get("w") or bbox.get("width") or 0)
        vh = int(bbox.get("h") or bbox.get("height") or 0)
        ix0, iy0 = max(ox, vx), max(oy, vy)
        ix1, iy1 = min(ox + ow, vx + vw), min(oy + oh, vy + vh)
        if ix1 <= ix0 or iy1 <= iy0:
            continue
        inter = (ix1 - ix0) * (iy1 - iy0)
        iou = inter / max(1, ow * oh + vw * vh - inter)
        if iou > best_iou:
            best_iou = iou
            best = vis
    return best, best_iou


def correlate_windows(
    os_windows: list[dict[str, Any]],
    vision_windows: list[dict[str, Any]],
    *,
    screen_width: int,
    screen_height: int,
) -> list[dict[str, Any]]:
    """Heuristic overlap between vdisplay bboxes and imgl vision regions."""
    rows: list[dict[str, Any]] = []
    for os_win in os_windows:
        ox = int(os_win.get("x") or 0)
        oy = int(os_win.get("y") or 0)
        ow = int(os_win.get("width") or 0)
        oh = int(os_win.get("height") or 0)
        best, best_iou = _best_vision_match(ox, oy, ow, oh, vision_windows)
        rows.append({
            "app_label": os_win.get("app_label") or os_win.get("title"),
            "window_id": os_win.get("window_id"),
            "os_bbox": {"x": ox, "y": oy, "width": ow, "height": oh},
            "monitor_name": os_win.get("monitor_name"),
            "nl": os_win.get("nl"),
            "suggested_imgl_window": suggest_imgl_region(os_win, screen_height=screen_height),
            "vision_match": best,
            "vision_iou": round(best_iou, 3),
        })
    return rows


def _build_report_recommendations(
    *,
    capture: dict[str, Any],
    window: str | None,
    target_os: dict[str, Any] | None,
    target_vision: dict[str, Any] | None,
    llm_ready: bool,
    height: int,
) -> list[str]:
    recs: list[str] = []
    if not llm_ready:
        recs.append("Ustaw OPENROUTER_API_KEY dla katalogu LLM (OpenRouter).")
    if not vdisplay_available():
        recs.append(vdisplay_missing_message())
    if capture.get("verdict") == "stale_capture":
        recs.append("Zrób świeży zrzut: imgl capture --interactive -o screen.png --verify")
    if target_os and not target_vision:
        recs.append(
            f"Okno OS '{target_os.get('app_label')}' — użyj IMGL_WINDOW="
            f"{suggest_imgl_region(target_os, screen_height=height or 1600)} lub --llm."
        )
    if window and not target_os and not target_vision:
        recs.append(f"Nie znaleziono okna '{window}' — sprawdź: make windows")
    return recs


def build_window_control_report(
    image: str | Path,
    *,
    window: str | None = None,
    locale: str = "pl",
) -> dict[str, Any]:
    """Combined diagnosis: capture autodiag + vdisplay + vision windows."""
    from imgl.autodiag import diagnose_capture

    image_path = Path(image).expanduser()
    capture = diagnose_capture(image_path, locale=locale)
    width = int(capture.get("width") or 0)
    height = int(capture.get("height") or 0)

    os_display = diagnose_os_display()
    os_windows = list_os_windows()
    vision_windows: list[dict[str, Any]] = []
    if image_path.is_file() and width and height:
        try:
            vision_windows = list_vision_windows(image_path)
        except Exception as exc:
            vision_windows = []
            capture.setdefault("warnings", []).append(f"vision_windows: {exc}")

    correlation = correlate_windows(os_windows, vision_windows, screen_width=width, screen_height=height)
    target_os = find_os_window(window) if window else None
    target_vision = next((item for item in vision_windows if item.get("id") == window), None)

    llm_ready = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
    recommendations = _build_report_recommendations(
        capture=capture, window=window, target_os=target_os,
        target_vision=target_vision, llm_ready=llm_ready, height=height,
    )

    return {
        "verdict": capture.get("verdict"),
        "image": str(image_path),
        "window": window,
        "capture": capture,
        "display": os_display,
        "os_windows": os_windows,
        "vision_windows": vision_windows,
        "correlation": correlation,
        "target_os_window": target_os,
        "target_vision_window": target_vision,
        "llm_ready": llm_ready,
        "recommendations": recommendations,
    }


__all__ = [
    "build_window_control_report",
    "correlate_windows",
    "default_display",
    "diagnose_os_display",
    "find_os_window",
    "list_os_monitors",
    "list_os_windows",
    "list_vision_windows",
    "suggest_imgl_region",
    "vdisplay_available",
    "vdisplay_missing_message",
]
