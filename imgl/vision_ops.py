"""Low-level image operations: template match and pixel diff."""

from __future__ import annotations

import io
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TemplateMatchResult:
    x: int
    y: int
    width: int
    height: int
    confidence: float
    method: str = "opencv-matchTemplate"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def template_available() -> tuple[bool, str]:
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
    except ImportError:
        return False, "opencv not installed (pip install opencv-python)"
    return True, "opencv template matching available"


def _png_to_gray_array(png: bytes):
    import cv2
    import numpy as np
    from PIL import Image

    image = Image.open(io.BytesIO(png)).convert("RGB")
    array = np.array(image)
    return cv2.cvtColor(array, cv2.COLOR_RGB2GRAY)


def _dedupe_matches(
    matches: list[TemplateMatchResult],
    *,
    min_distance: int,
) -> list[TemplateMatchResult]:
    deduped: list[TemplateMatchResult] = []
    for item in matches:
        cx = item.x + item.width // 2
        cy = item.y + item.height // 2
        if any(
            abs(cx - (kept.x + kept.width // 2)) < min_distance
            and abs(cy - (kept.y + kept.height // 2)) < min_distance
            for kept in deduped
        ):
            continue
        deduped.append(item)
    return deduped


def match_template_png(
    png: bytes,
    template_png: bytes,
    *,
    threshold: float = 0.85,
    method: str = "ccoeff_normed",
) -> list[TemplateMatchResult]:
    """Find template occurrences in a screenshot using OpenCV matchTemplate."""
    ready, reason = template_available()
    if not ready:
        raise RuntimeError(reason)

    import cv2
    import numpy as np

    screen = _png_to_gray_array(png)
    template = _png_to_gray_array(template_png)
    th, tw = template.shape[:2]
    if th <= 0 or tw <= 0:
        raise ValueError("template image has invalid dimensions")
    if screen.shape[0] < th or screen.shape[1] < tw:
        return []

    cv_method = {
        "ccoeff_normed": cv2.TM_CCOEFF_NORMED,
        "sqdiff_normed": cv2.TM_SQDIFF_NORMED,
    }.get(method, cv2.TM_CCOEFF_NORMED)

    result = cv2.matchTemplate(screen, template, cv_method)
    if cv_method == cv2.TM_SQDIFF_NORMED:
        locations = np.where(result <= (1.0 - threshold))
        scores = 1.0 - result[locations]
    else:
        locations = np.where(result >= threshold)
        scores = result[locations]

    matches: list[TemplateMatchResult] = []
    for y, x, confidence in zip(locations[0], locations[1], scores, strict=False):
        matches.append(
            TemplateMatchResult(
                x=int(x),
                y=int(y),
                width=int(tw),
                height=int(th),
                confidence=float(confidence),
            )
        )

    if not matches and cv_method != cv2.TM_SQDIFF_NORMED:
        _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
        if float(max_val) >= threshold:
            x, y = max_loc
            matches.append(
                TemplateMatchResult(
                    x=int(x),
                    y=int(y),
                    width=int(tw),
                    height=int(th),
                    confidence=float(max_val),
                )
            )

    matches.sort(key=lambda item: item.confidence, reverse=True)
    return _dedupe_matches(matches, min_distance=max(tw, th) // 2)[:16]


def diff_png_bytes(
    before: bytes,
    after: bytes,
    *,
    region: tuple[int, int, int, int] | None = None,
    min_changed_ratio: float = 0.001,
    min_changed_pixels: int = 0,
) -> dict[str, Any]:
    """Compare two PNG payloads and report whether they differ meaningfully."""
    compare_region = region
    if compare_region is not None:
        before = _crop_png_region(before, compare_region)
        after = _crop_png_region(after, compare_region)

    if before == after:
        return {
            "verified": False,
            "changed_ratio": 0.0,
            "changed_pixels": 0,
            "total_pixels": 0,
            "method": "bytes",
            "compare_region": compare_region,
        }

    try:
        from PIL import Image
    except ImportError:
        return {
            "verified": True,
            "changed_ratio": 1.0,
            "changed_pixels": None,
            "total_pixels": None,
            "method": "bytes",
            "compare_region": compare_region,
        }

    before_image = Image.open(io.BytesIO(before)).convert("RGB")
    after_image = Image.open(io.BytesIO(after)).convert("RGB")
    if before_image.size != after_image.size:
        after_image = after_image.resize(before_image.size)

    width, height = before_image.size
    total_pixels = width * height
    changed_pixels = 0
    before_pixels = before_image.get_flattened_data()
    after_pixels = after_image.get_flattened_data()
    for left, right in zip(before_pixels, after_pixels, strict=False):
        if left != right:
            changed_pixels += 1
    changed_ratio = changed_pixels / total_pixels if total_pixels else 0.0
    verified = changed_pixels > 0 if compare_region is not None else False
    if not verified:
        verified = changed_pixels >= min_changed_pixels or changed_ratio >= min_changed_ratio
    return {
        "verified": verified,
        "changed_ratio": round(changed_ratio, 6),
        "changed_pixels": changed_pixels,
        "total_pixels": total_pixels,
        "method": "pil",
        "compare_region": compare_region,
    }


def _crop_png_region(png: bytes, region: tuple[int, int, int, int]) -> bytes:
    from PIL import Image

    x, y, width, height = region
    image = Image.open(io.BytesIO(png)).convert("RGB")
    cropped = image.crop((x, y, x + width, y + height))
    out = io.BytesIO()
    cropped.save(out, format="PNG")
    return out.getvalue()


@dataclass(frozen=True)
class MatchOverlayItem:
    index: int
    x: int
    y: int
    width: int
    height: int
    label: str
    confidence: float
    selected: bool = False
    rejected: bool = False


def _confidence_color(
    confidence: float,
    *,
    selected: bool = False,
    rejected: bool = False,
) -> tuple[int, int, int]:
    if rejected:
        return (140, 140, 140)
    if selected:
        return (0, 220, 80)
    if confidence >= 0.9:
        return (0, 180, 255)
    if confidence >= 0.75:
        return (255, 180, 0)
    return (255, 70, 70)


def render_match_overlay_png(
    png: bytes,
    matches: list[MatchOverlayItem],
    *,
    selected_index: int | None = None,
    rejected: list[MatchOverlayItem] | None = None,
) -> bytes:
    """Draw numbered bounding boxes and confidence labels on a screenshot."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("Pillow not installed (pip install Pillow)") from exc

    base = Image.open(io.BytesIO(png)).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.load_default(size=12)
    except TypeError:
        font = ImageFont.load_default()

    all_items = list(matches)
    if rejected:
        all_items.extend(rejected)

    for item in all_items:
        x1, y1 = item.x, item.y
        x2, y2 = item.x + item.width, item.y + item.height
        selected = item.selected or (
            selected_index is not None and item.index == selected_index and not item.rejected
        )
        color = _confidence_color(item.confidence, selected=selected, rejected=item.rejected)
        width = 4 if selected else 2
        draw.rectangle([x1, y1, x2, y2], outline=(*color, 255), width=width)
        prefix = "R" if item.rejected else str(item.index)
        tag = f"#{prefix} {item.confidence:.2f} {item.label}"[:56]
        text_y = max(0, y1 - 14)
        draw.rectangle([x1, text_y, x1 + min(220, len(tag) * 7 + 8), text_y + 14], fill=(0, 0, 0, 180))
        draw.text((x1 + 2, text_y + 1), tag, fill=(*color, 255), font=font)
        cx = item.x + item.width // 2
        cy = item.y + item.height // 2
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(*color, 255))

    composed = Image.alpha_composite(base, overlay)
    out = io.BytesIO()
    composed.convert("RGB").save(out, format="PNG")
    return out.getvalue()
