"""Geometry helpers for bounding boxes."""

from __future__ import annotations

from imgl.types import BBox


def iou(a: BBox, b: BBox) -> float:
    ax0, ay0, ax1, ay1 = a.as_xyxy()
    bx0, by0, bx1, by1 = b.as_xyxy()
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    area_a = a.w * a.h
    area_b = b.w * b.h
    return inter / max(1, area_a + area_b - inter)


def center_in(inner: BBox, outer: BBox) -> bool:
    cx = inner.x + inner.w / 2
    cy = inner.y + inner.h / 2
    ox0, oy0, ox1, oy1 = outer.as_xyxy()
    return ox0 <= cx <= ox1 and oy0 <= cy <= oy1


def bbox_distance(a: BBox, b: BBox) -> float:
    ax = a.x + a.w / 2
    ay = a.y + a.h / 2
    bx = b.x + b.w / 2
    by = b.y + b.h / 2
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def bbox_from_xyxy(x0: int, y0: int, x1: int, y1: int) -> BBox:
    return BBox.from_xyxy(x0, y0, x1, y1)
