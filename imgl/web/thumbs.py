"""Crop thumbnails for catalog actions and windows."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from imgl.paths import resolve_image_path


def _clamp_box(
    bbox: dict[str, int],
    *,
    width: int,
    height: int,
    padding: int = 10,
) -> tuple[int, int, int, int]:
    x0 = max(0, bbox["x"] - padding)
    y0 = max(0, bbox["y"] - padding)
    x1 = min(width, bbox["x"] + bbox["w"] + padding)
    y1 = min(height, bbox["y"] + bbox["h"] + padding)
    if x1 <= x0:
        x1 = min(width, x0 + 48)
    if y1 <= y0:
        y1 = min(height, y0 + 32)
    return x0, y0, x1, y1


def crop_bbox_png(
    image_path: str | Path,
    bbox: dict[str, int],
    *,
    max_dim: int = 160,
    padding: int = 10,
) -> bytes:
    """Return PNG bytes for a bbox crop, scaled to max_dim."""
    path = resolve_image_path(image_path)
    with Image.open(path) as img:
        x0, y0, x1, y1 = _clamp_box(bbox, width=img.width, height=img.height, padding=padding)
        crop = img.crop((x0, y0, x1, y1)).convert("RGB")
    w, h = crop.size
    scale = min(1.0, max_dim / max(w, h, 1))
    if scale < 1.0:
        crop = crop.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
    buf = BytesIO()
    crop.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def window_bbox_dict(window: Any) -> dict[str, int]:
    bbox = window.bbox
    return {"x": bbox.x, "y": bbox.y, "w": bbox.w, "h": bbox.h}
