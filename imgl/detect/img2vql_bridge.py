"""Optional bridge to img2vql when installed."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from imgl.detect.local import DetectedUI, detect_ui_elements as detect_local
from imgl.geometry import bbox_from_xyxy
from imgl.types import BBox

if TYPE_CHECKING:
    pass


def img2vql_available() -> bool:
    try:
        import img2vql  # noqa: F401

        return True
    except ImportError:
        return False


def _from_img2vql_dict(raw: dict) -> DetectedUI:
    x0, y0, x1, y1 = raw["bbox"]
    return DetectedUI(
        id=raw["id"],
        role=raw["role"],
        bbox=bbox_from_xyxy(x0, y0, x1, y1),
        confidence=float(raw.get("confidence", 0.5)),
        label=raw.get("label", ""),
        metadata=dict(raw.get("metadata", {})),
    )


def detect_with_img2vql(image_path: str | Path) -> list[DetectedUI] | None:
    """Run img2vql detection if the package is available."""
    if not img2vql_available():
        return None

    from img2vql import detect_ui_elements as img2vql_detect

    result = img2vql_detect(image_path)
    if not result.get("ok"):
        return None
    return [_from_img2vql_dict(item) for item in result.get("elements", [])]


def detect_ui_merged(
    image: Image.Image,
    *,
    source_path: str | None = None,
    prefer_img2vql: bool = True,
) -> tuple[list[DetectedUI], str]:
    """Detect UI elements using img2vql when possible, else local heuristics."""
    if prefer_img2vql and source_path:
        external = detect_with_img2vql(source_path)
        if external:
            return external, "img2vql"

    return detect_local(image), "local"
