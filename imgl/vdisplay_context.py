"""Import vdisplay ScreenContext payloads into IMGL scene metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from imgl.types import Scene


def from_vdisplay_context(
    payload: dict[str, Any],
    *,
    analyze: bool = True,
    lang: str = "eng+pol",
) -> dict[str, Any]:
    """Merge vdisplay ScreenContext into IMGL scene metadata.

    Returns ``{"ok": bool, "scene": dict|None, "metadata": dict, "error": str|None}``.
    """
    image_path = str(payload.get("image_path") or payload.get("capture", {}).get("path") or "")
    path = Path(image_path).expanduser()
    metadata = _metadata_from_context(payload)

    if not path.is_file():
        return {"ok": False, "scene": None, "metadata": metadata, "error": f"image not found: {path}"}

    imgl_block = payload.get("imgl") or {}
    if isinstance(imgl_block, dict) and imgl_block.get("ok") and imgl_block.get("scene"):
        scene_dict = dict(imgl_block["scene"])
        scene_dict.setdefault("metadata", {})
        scene_dict["metadata"] = {**scene_dict.get("metadata", {}), **metadata}
        return {"ok": True, "scene": scene_dict, "metadata": metadata, "error": None}

    if not analyze:
        return {"ok": True, "scene": None, "metadata": metadata, "error": None}

    try:
        from imgl.pipeline import analyze as imgl_analyze
        from imgl.export.json_export import scene_to_json
    except ImportError as exc:
        return {"ok": False, "scene": None, "metadata": metadata, "error": str(exc)}

    scene = imgl_analyze(str(path), lang=lang)
    scene.metadata.update(metadata)
    return {
        "ok": True,
        "scene": scene_to_json(scene),
        "metadata": metadata,
        "error": None,
    }


def enrich_scene_from_vdisplay(scene: Scene, payload: dict[str, Any]) -> Scene:
    scene.metadata.update(_metadata_from_context(payload))
    return scene


def _metadata_from_context(payload: dict[str, Any]) -> dict[str, Any]:
    capture = dict(payload.get("capture") or {})
    environment = dict(payload.get("environment") or {})
    block: dict[str, Any] = {
        "source": "vdisplay",
        "fingerprint": payload.get("fingerprint"),
        "observed_at": payload.get("observed_at"),
        "capture": capture,
        "environment": environment,
    }
    if payload.get("map_pack"):
        block["gui_map"] = payload["map_pack"]
    if payload.get("verify"):
        block["verify"] = payload["verify"]
    if payload.get("vision"):
        block["vision"] = payload["vision"]
    if payload.get("nl"):
        block["nl"] = payload["nl"]
    routing = environment.get("routing")
    if isinstance(routing, dict):
        block["routing"] = routing
    return block
