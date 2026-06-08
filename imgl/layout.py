"""Layout grouping: windows, OCR assignment, titles."""

from __future__ import annotations

from imgl.detect.local import DetectedUI
from imgl.geometry import center_in
from imgl.types import BBox, OcrBox, Window


def build_windows(
    detected: list[DetectedUI],
    *,
    width: int,
    height: int,
) -> list[Window]:
    """Build Window list from detected panels/windows, or fallback to full screen."""
    window_like = [item for item in detected if item.role in {"window", "panel"}]
    window_like.sort(key=lambda item: item.bbox.w * item.bbox.h, reverse=True)

    if not window_like:
        return [
            Window(
                id="win-screen",
                bbox=BBox(x=0, y=0, w=width, h=height),
                title=None,
                z=0,
                elements=[],
            )
        ]

    windows: list[Window] = []
    for index, item in enumerate(window_like):
        windows.append(
            Window(
                id=item.id if item.id else f"win-{index}",
                bbox=item.bbox,
                title=None,
                z=len(window_like) - index,
                elements=[],
            )
        )
    return windows


def find_containing_window(bbox: BBox, windows: list[Window]) -> Window | None:
    """Return the smallest window that contains the bbox center."""
    matches = [window for window in windows if center_in(bbox, window.bbox)]
    if not matches:
        return None
    return min(matches, key=lambda window: window.bbox.w * window.bbox.h)


def assign_ocr_to_windows(
    windows: list[Window],
    ocr_boxes: list[OcrBox],
) -> tuple[list[Window], list[OcrBox]]:
    """Attach unassigned OCR boxes to windows; return orphans."""
    orphans: list[OcrBox] = []
    buckets: dict[str, list[OcrBox]] = {window.id: [] for window in windows}

    for box in ocr_boxes:
        window = find_containing_window(box.bbox, windows)
        if window is None:
            orphans.append(box)
        else:
            buckets[window.id].append(box)

    return windows, orphans


def extract_window_titles(
    windows: list[Window],
    detected: list[DetectedUI],
    ocr_boxes: list[OcrBox],
) -> None:
    """Set window.title from OCR inside titlebar regions overlapping each window."""
    titlebars = [item for item in detected if item.role == "titlebar"]
    if not titlebars:
        return

    for window in windows:
        titlebar = _best_titlebar_for_window(window.bbox, titlebars)
        if titlebar is None:
            continue
        texts = [
            box.text
            for box in ocr_boxes
            if center_in(box.bbox, titlebar.bbox) and center_in(box.bbox, window.bbox)
        ]
        if texts:
            window.title = " ".join(texts)


def _best_titlebar_for_window(window_bbox: BBox, titlebars: list[DetectedUI]) -> DetectedUI | None:
    matches = [
        bar
        for bar in titlebars
        if center_in(bar.bbox, window_bbox) or _overlaps_top(window_bbox, bar.bbox)
    ]
    if not matches:
        return None
    return max(matches, key=lambda bar: bar.confidence)


def _overlaps_top(window_bbox: BBox, bar_bbox: BBox) -> bool:
    _, wy0, _, wy1 = window_bbox.as_xyxy()
    _, by0, _, by1 = bar_bbox.as_xyxy()
    return by0 <= wy0 + (wy1 - wy0) * 0.15 and by1 >= wy0
