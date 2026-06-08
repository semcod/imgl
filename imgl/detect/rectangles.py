"""Detect rectangular UI frames (inputs, bordered controls)."""

from __future__ import annotations

from PIL import Image, ImageFilter

from imgl.geometry import bbox_from_xyxy, iou
from imgl.types import BBox


def detect_input_frames(
    image: Image.Image,
    *,
    scan_w: int = 480,
    max_frames: int = 32,
) -> list[BBox]:
    """
    Find hollow or lightly-filled rectangles that may be text inputs.

    Uses edge emphasis on a downsampled grayscale image.
    """
    w, h = image.size
    scale = min(1.0, scan_w / w)
    sw, sh = max(48, int(w * scale)), max(48, int(h * scale))
    small = image.resize((sw, sh)).convert("L")
    edges = small.filter(ImageFilter.FIND_EDGES)
    pixels = list(edges.get_flattened_data())

    mask = [[pixels[y * sw + x] > 40 for x in range(sw)] for y in range(sh)]
    rects = _find_rectangular_frames(mask)

    frames: list[BBox] = []
    for x0, y0, x1, y1 in rects:
        rw, rh = x1 - x0, y1 - y0
        if rw < 8 or rh < 4:
            continue
        aspect = rw / rh
        if aspect < 2.0 or aspect > 18:
            continue
        if rh > sh * 0.1 or rw > sw * 0.75:
            continue

        fx0, fy0 = int(x0 / scale), int(y0 / scale)
        fx1, fy1 = int(x1 / scale), int(y1 / scale)
        candidate = bbox_from_xyxy(fx0, fy0, fx1, fy1)
        if candidate.w < 40 or candidate.h < 16:
            continue
        if any(iou(candidate, existing) > 0.5 for existing in frames):
            continue
        frames.append(candidate)

    frames.sort(key=lambda box: box.w * box.h, reverse=True)
    return frames[:max_frames]


def _find_rectangular_frames(mask: list[list[bool]]) -> list[tuple[int, int, int, int]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    rects: list[tuple[int, int, int, int]] = []

    for y in range(1, height - 2):
        for x in range(1, width - 2):
            if not _looks_like_frame(mask, x, y, width, height):
                continue
            x1 = x
            while x1 < width - 1 and _column_has_edge(mask, x1, y, height):
                x1 += 1
            y1 = y
            while y1 < height - 1 and _row_has_edge(mask, x, y1, width):
                y1 += 1
            if x1 - x < 6 or y1 - y < 3:
                continue
            rects.append((x, y, x1, y1))

    return rects


def _looks_like_frame(mask: list[list[bool]], x: int, y: int, width: int, height: int) -> bool:
    if not mask[y][x]:
        return False
    edge_hits = 0
    for dx in range(x, min(width, x + 8)):
        if mask[y][dx]:
            edge_hits += 1
    for dy in range(y, min(height, y + 4)):
        if mask[dy][x]:
            edge_hits += 1
    return edge_hits >= 4


def _column_has_edge(mask: list[list[bool]], x: int, y: int, height: int) -> bool:
    return any(mask[yy][x] for yy in range(y, min(height, y + 6)))


def _row_has_edge(mask: list[list[bool]], x: int, y: int, width: int) -> bool:
    return any(mask[y][xx] for xx in range(x, min(width, x + 12)))
