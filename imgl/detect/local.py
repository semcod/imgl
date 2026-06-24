"""Standalone UI detection without external CV models."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from PIL import Image

from imgl.geometry import bbox_from_xyxy
from imgl.types import BBox


@dataclass
class DetectedUI:
    id: str
    role: str
    bbox: BBox
    confidence: float = 0.5
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _hex_color(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def _avg_color(im: Image.Image, x0: int, y0: int, x1: int, y1: int) -> tuple[int, int, int]:
    crop = im.crop((x0, y0, x1, y1)).convert("RGB")
    pixels = list(crop.get_flattened_data())
    if not pixels:
        return (0, 0, 0)
    count = len(pixels)
    r = sum(p[0] for p in pixels) // count
    g = sum(p[1] for p in pixels) // count
    b = sum(p[2] for p in pixels) // count
    return (r, g, b)


def _iou_xyxy(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = (ax1 - ax0) * (ay1 - ay0)
    area_b = (bx1 - bx0) * (by1 - by0)
    return inter / max(1, area_a + area_b - inter)


def _detect_titlebar(im: Image.Image, w: int, h: int) -> DetectedUI | None:
    band_h = max(20, int(h * 0.045))
    if band_h >= h // 2:
        return None
    top_rgb = _avg_color(im, 0, 0, w, band_h)
    below_rgb = _avg_color(im, 0, band_h, w, min(h, band_h * 3))
    diff = sum(abs(a - b) for a, b in zip(top_rgb, below_rgb, strict=True))
    if diff < 18:
        return None
    return DetectedUI(
        id="titlebar_0",
        role="titlebar",
        bbox=bbox_from_xyxy(0, 0, w, band_h),
        confidence=0.72 if diff > 40 else 0.55,
        label="window title bar",
        metadata={"source": "titlebar_band", "color": _hex_color(top_rgb)},
    )


def _flood_rects(
    mask: list[list[bool]],
    *,
    min_area: int,
    max_area: int,
) -> list[tuple[int, int, int, int]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    rects: list[tuple[int, int, int, int]] = []

    for y in range(height):
        for x in range(width):
            if seen[y][x] or not mask[y][x]:
                continue
            queue: deque[tuple[int, int]] = deque([(x, y)])
            seen[y][x] = True
            min_x = max_x = x
            min_y = max_y = y
            area = 0
            while queue:
                cx, cy = queue.popleft()
                area += 1
                min_x, max_x = min(min_x, cx), max(max_x, cx)
                min_y, max_y = min(min_y, cy), max(max_y, cy)
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx] and mask[ny][nx]:
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            if min_area <= area <= max_area:
                rects.append((min_x, min_y, max_x + 1, max_y + 1))
    return rects


def _prepare_button_scan(
    im: Image.Image,
    w: int,
    h: int,
    *,
    scan_w: int,
) -> tuple[Image.Image, float, int, int]:
    scale = min(1.0, scan_w / w)
    sw, sh = max(32, int(w * scale)), max(32, int(h * scale))
    return im.resize((sw, sh)).convert("RGB"), scale, sw, sh


def _neighbor_avg_rgb(
    pixels: list[tuple[int, int, int]],
    *,
    sw: int,
    x: int,
    y: int,
) -> tuple[int, int, int]:
    neighbors: list[tuple[int, int, int]] = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            neighbors.append(pixels[(y + dy) * sw + (x + dx)])
    return tuple(sum(color[i] for color in neighbors) // len(neighbors) for i in range(3))


def _build_contrast_mask(
    pixels: list[tuple[int, int, int]],
    *,
    sw: int,
    sh: int,
    threshold: int = 28,
) -> list[list[bool]]:
    mask = [[False] * sw for _ in range(sh)]
    for y in range(1, sh - 1):
        for x in range(1, sw - 1):
            r, g, b = pixels[y * sw + x]
            avg = _neighbor_avg_rgb(pixels, sw=sw, x=x, y=y)
            diff = sum(abs(a - b) for a, b in zip((r, g, b), avg, strict=True))
            mask[y][x] = diff > threshold
    return mask


def _button_blob_area_limits(sw: int, sh: int) -> tuple[int, int]:
    total = sw * sh
    min_area = max(4, int(total * 0.00015))
    max_area = max(min_area + 1, int(total * 0.012))
    return min_area, max_area


def _valid_button_blob_size(rw: int, rh: int) -> bool:
    if rw < 2 or rh < 2:
        return False
    aspect = rw / rh
    return 0.25 <= aspect <= 6.0


def _scale_blob_rect(
    rect: tuple[int, int, int, int],
    scale: float,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = rect
    return int(x0 / scale), int(y0 / scale), int(x1 / scale), int(y1 / scale)


def _overlaps_seen_button(
    box: tuple[int, int, int, int],
    seen_boxes: list[tuple[int, int, int, int]],
    *,
    min_iou: float = 0.6,
) -> bool:
    return any(_iou_xyxy(box, seen) > min_iou for seen in seen_boxes)


def _button_confidence(
    aspect: float,
    bw: int,
    bh: int,
    *,
    image_w: int,
    image_h: int,
) -> float:
    if 1.5 <= aspect <= 4.0 and 18 <= bw <= image_w * 0.25 and 14 <= bh <= image_h * 0.08:
        return 0.68
    return 0.45


def _button_role(aspect: float, bw: int, bh: int) -> str:
    if bw <= 36 and bh <= 36 and 0.7 <= aspect <= 1.4:
        return "icon_button"
    return "button"


def _button_from_blob_rect(
    im: Image.Image,
    rect: tuple[int, int, int, int],
    *,
    scale: float,
    image_w: int,
    image_h: int,
    seen_boxes: list[tuple[int, int, int, int]],
    element_index: int,
) -> DetectedUI | None:
    x0, y0, x1, y1 = rect
    rw, rh = x1 - x0, y1 - y0
    if not _valid_button_blob_size(rw, rh):
        return None

    fx0, fy0, fx1, fy1 = _scale_blob_rect(rect, scale)
    box = (fx0, fy0, fx1, fy1)
    if _overlaps_seen_button(box, seen_boxes):
        return None

    aspect = rw / rh
    bw, bh = fx1 - fx0, fy1 - fy0
    role = _button_role(aspect, bw, bh)
    rgb = _avg_color(im, fx0, fy0, fx1, fy1)
    return DetectedUI(
        id=f"{role}_{element_index}",
        role=role,
        bbox=bbox_from_xyxy(fx0, fy0, fx1, fy1),
        confidence=_button_confidence(aspect, bw, bh, image_w=image_w, image_h=image_h),
        label=role.replace("_", " "),
        metadata={"source": "contrast_blob", "color": _hex_color(rgb), "aspect": round(aspect, 2)},
    )


def _rank_button_detections(elements: list[DetectedUI], *, limit: int = 24) -> list[DetectedUI]:
    elements.sort(key=lambda item: (-item.confidence, -(item.bbox.w * item.bbox.h)))
    return elements[:limit]


def _detect_buttons(im: Image.Image, w: int, h: int, *, scan_w: int = 320) -> list[DetectedUI]:
    small, scale, sw, sh = _prepare_button_scan(im, w, h, scan_w=scan_w)
    pixels = list(small.get_flattened_data())

    mask = _build_contrast_mask(pixels, sw=sw, sh=sh)
    min_area, max_area = _button_blob_area_limits(sw, sh)
    rects = _flood_rects(mask, min_area=min_area, max_area=max_area)

    elements: list[DetectedUI] = []
    seen_boxes: list[tuple[int, int, int, int]] = []
    for rect in rects:
        detected = _button_from_blob_rect(
            im,
            rect,
            scale=scale,
            image_w=w,
            image_h=h,
            seen_boxes=seen_boxes,
            element_index=len(elements),
        )
        if detected is None:
            continue
        seen_boxes.append(detected.bbox.as_xyxy())
        elements.append(detected)

    return _rank_button_detections(elements)


def _flood_fill_bbox(
    cells: list[tuple[int, int, int, int, tuple[int, int, int]]],
    start_idx: int,
    used: list[bool],
    cell_w: int,
    cell_h: int,
) -> tuple[int, int, int, int]:
    x0, y0, x1, y1, _ = cells[start_idx]
    stack = [start_idx]
    used[start_idx] = True
    min_x, min_y, max_x, max_y = x0, y0, x1, y1
    while stack:
        current = stack.pop()
        cx0, cy0, cx1, cy1, crgb = cells[current]
        min_x, min_y = min(min_x, cx0), min(min_y, cy0)
        max_x, max_y = max(max_x, cx1), max(max_y, cy1)
        for other, (ox0, oy0, ox1, oy1, orgb) in enumerate(cells):
            if used[other]:
                continue
            if sum(abs(a - b) for a, b in zip(crgb, orgb, strict=True)) > 24:
                continue
            touches = not (ox1 < min_x or ox0 > max_x or oy1 < min_y or oy0 > max_y)
            adjacent = (
                abs(ox0 - max_x) <= cell_w
                or abs(ox1 - min_x) <= cell_w
                or abs(oy0 - max_y) <= cell_h
                or abs(oy1 - min_y) <= cell_h
            )
            if touches or adjacent:
                used[other] = True
                stack.append(other)
    return min_x, min_y, max_x, max_y


def _detect_panels_simple(im: Image.Image, w: int, h: int, *, grid: int = 12) -> list[DetectedUI]:
    """Coarse grid color clustering for large window-like regions."""
    cell_w = max(1, w // grid)
    cell_h = max(1, h // grid)
    cells: list[tuple[int, int, int, int, tuple[int, int, int]]] = []

    for gy in range(grid):
        for gx in range(grid):
            x0, y0 = gx * cell_w, gy * cell_h
            x1, y1 = min(w, x0 + cell_w), min(h, y0 + cell_h)
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            rgb = _avg_color(im, x0, y0, x1, y1)
            cells.append((x0, y0, x1, y1, rgb))

    if not cells:
        return []

    used = [False] * len(cells)
    regions: list[DetectedUI] = []
    for index in range(len(cells)):
        if used[index]:
            continue
        min_x, min_y, max_x, max_y = _flood_fill_bbox(cells, index, used, cell_w, cell_h)
        area_ratio = ((max_x - min_x) * (max_y - min_y)) / max(1, w * h)
        if area_ratio < 0.12:
            continue
        role = "window" if area_ratio >= 0.25 else "panel"
        regions.append(DetectedUI(
            id=f"{role}_{len(regions)}",
            role=role,
            bbox=bbox_from_xyxy(min_x, min_y, max_x, max_y),
            confidence=min(0.9, 0.5 + area_ratio),
            label=f"{role} region",
            metadata={"source": "color_grid", "area_ratio": round(area_ratio, 3)},
        ))

    return regions


def _dedupe(elements: list[DetectedUI]) -> list[DetectedUI]:
    elements = sorted(elements, key=lambda item: (-item.confidence, -(item.bbox.w * item.bbox.h)))
    kept: list[DetectedUI] = []
    for element in elements:
        if any(
            element.role != other.role and _iou_xyxy(element.bbox.as_xyxy(), other.bbox.as_xyxy()) > 0.75
            for other in kept
        ):
            continue
        if any(
            element.role == other.role and _iou_xyxy(element.bbox.as_xyxy(), other.bbox.as_xyxy()) > 0.85
            for other in kept
        ):
            continue
        kept.append(element)
    return kept


def detect_ui_elements(
    image: Image.Image,
    *,
    detect_buttons: bool = True,
    detect_panels: bool = True,
) -> list[DetectedUI]:
    """Detect titlebar, panels, windows and buttons on a screenshot."""
    w, h = image.size
    elements: list[DetectedUI] = []

    titlebar = _detect_titlebar(image, w, h)
    if titlebar:
        elements.append(titlebar)

    if detect_panels:
        elements.extend(_detect_panels_simple(image, w, h))

    if detect_buttons:
        elements.extend(_detect_buttons(image, w, h))

    return _dedupe(elements)
