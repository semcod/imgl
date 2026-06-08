"""Discover application windows on a screenshot and crop per-window regions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image

from imgl.geometry import center_in
from imgl.layout import find_containing_window
from imgl.paths import resolve_image_path
from imgl.types import BBox, Element, OcrBox, Scene, Window

_INTERACTIVE_TYPES = {"button", "icon_button", "input", "toolbar", "label"}


@dataclass
class WindowSummary:
    """One discoverable window region with stats for the picker UI."""

    index: int
    window: Window
    element_count: int
    interactive_count: int
    crop_path: str | None = None
    annotated_path: str | None = None

    @property
    def label(self) -> str:
        return self.window.title or self.window.id

    @property
    def bbox(self) -> BBox:
        return self.window.bbox


def is_monolithic_scene(scene: Scene, *, min_area_ratio: float = 0.85) -> bool:
    if len(scene.windows) != 1:
        return False
    window = scene.windows[0]
    total = max(1, scene.width * scene.height)
    area = window.bbox.w * window.bbox.h
    return area / total >= min_area_ratio


def apply_discovered_windows(scene: Scene) -> Scene:
    """Replace scene.windows with heuristically discovered regions."""
    discovered = discover_windows(scene)
    return Scene(
        width=scene.width,
        height=scene.height,
        source_image=scene.source_image,
        windows=discovered,
        orphan_elements=scene.orphan_elements,
        ocr_boxes=scene.ocr_boxes,
        metadata={
            **scene.metadata,
            "windows_discovered": True,
            "window_count": len(discovered),
        },
    )


def discover_windows(scene: Scene) -> list[Window]:
    """
    Return window regions for user selection.

    When detection yields one full-screen window, split it heuristically using
    element layout (vertical/horizontal gutters).
    """
    if is_monolithic_scene(scene):
        return _split_monolithic_window(scene)
    return sorted(scene.windows, key=lambda item: (-item.z, item.bbox.y, item.bbox.x))


def summarize_windows(
    scene: Scene,
    *,
    crop_dir: str | Path | None = None,
    image_path: str | None = None,
) -> list[WindowSummary]:
    windows = discover_windows(scene)
    summaries: list[WindowSummary] = []
    for index, window in enumerate(windows, start=1):
        interactive = [
            element
            for element in window.elements
            if element.type in _INTERACTIVE_TYPES
        ]
        crop_path = None
        if crop_dir and image_path:
            crop_path = str(
                export_window_crop(
                    image_path,
                    window,
                    output_dir=crop_dir,
                )
            )
        summaries.append(
            WindowSummary(
                index=index,
                window=window,
                element_count=len(window.elements),
                interactive_count=len(interactive),
                crop_path=crop_path,
            )
        )
    return summaries


def format_window_picker(summaries: list[WindowSummary], *, scene: Scene) -> str:
    if not summaries:
        return "Brak wykrytych okien."

    lines = [
        "",
        f"=== Wykryte okna ({len(summaries)}) — wybierz region do analizy ===",
        f"Ekran: {scene.width}×{scene.height}px",
        "",
    ]
    for item in summaries:
        bbox = item.bbox
        title = item.label
        lines.append(
            f"  {item.index:3d}. {title} "
            f"@ ({bbox.x}, {bbox.y}) {bbox.w}×{bbox.h}px "
            f"[{item.interactive_count} interaktywnych / {item.element_count} elementów]"
        )
        if item.crop_path:
            lines.append(f"       wycinek: {item.crop_path}")
    lines.extend(
        [
            "",
            "Wpisz numer okna, 'podglad' (wycinki PNG), 'wszystkie' (cały ekran), lub 'quit'.",
            "",
        ]
    )
    return "\n".join(lines)


def get_discovered_window(scene: Scene, window_ref: str | int) -> Window | None:
    windows = discover_windows(scene)
    if isinstance(window_ref, int):
        if 1 <= window_ref <= len(windows):
            return windows[window_ref - 1]
        return None

    ref = str(window_ref).strip().casefold()
    for window in windows:
        if window.id.casefold() == ref:
            return window
        title = (window.title or "").casefold()
        if title and title == ref:
            return window
    return None


def scene_for_window(scene: Scene, window: Window) -> Scene:
    """Narrow scene to one window: bbox, elements, and OCR inside the region."""
    elements = [element for element in window.elements]
    ocr_boxes = [
        box
        for box in scene.ocr_boxes
        if center_in(box.bbox, window.bbox)
    ]
    return Scene(
        width=window.bbox.w,
        height=window.bbox.h,
        source_image=scene.source_image,
        windows=[
            Window(
                id=window.id,
                bbox=BBox(x=0, y=0, w=window.bbox.w, h=window.bbox.h),
                title=window.title,
                z=window.z,
                elements=_shift_elements(elements, window.bbox),
            )
        ],
        orphan_elements=[],
        ocr_boxes=_shift_ocr_boxes(ocr_boxes, window.bbox),
        metadata={
            **scene.metadata,
            "window_scope": window.id,
            "window_origin": {"x": window.bbox.x, "y": window.bbox.y},
        },
    )


def crop_window_image(image_path: str | Path, window: Window) -> Image.Image:
    image = Image.open(resolve_image_path(image_path)).convert("RGB")
    x0, y0, x1, y1 = window.bbox.as_xyxy()
    width, height = image.size
    x0 = max(0, min(width, x0))
    y0 = max(0, min(height, y0))
    x1 = max(x0 + 1, min(width, x1))
    y1 = max(y0 + 1, min(height, y1))
    return image.crop((x0, y0, x1, y1))


def export_window_crop(
    image_path: str | Path,
    window: Window,
    *,
    output_dir: str | Path | None = None,
) -> Path:
    source = Path(resolve_image_path(image_path))
    out_dir = Path(output_dir) if output_dir else source.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_id = _safe_filename(window.id)
    out = out_dir / f"{source.stem}.{safe_id}{source.suffix or '.png'}"
    crop_window_image(source, window).save(out, format="PNG")
    return out.resolve()


def default_window_annotated_path(image_path: str | Path, window_id: str) -> Path:
    source = Path(image_path)
    safe_id = _safe_filename(window_id)
    return source.with_name(f"{source.stem}.{safe_id}.numbered{source.suffix or '.png'}")


def _split_monolithic_window(scene: Scene) -> list[Window]:
    window = scene.windows[0]
    elements = _collect_elements(scene)
    if len(elements) < 8:
        window.title = window.title or _guess_window_title(window, scene.ocr_boxes)
        return [window]

    vertical_split = _best_vertical_split(elements, window.bbox, scene.width)
    columns: list[BBox]
    if vertical_split is not None:
        split_x = vertical_split
        columns = [
            BBox(x=window.bbox.x, y=window.bbox.y, w=split_x - window.bbox.x, h=window.bbox.h),
            BBox(x=split_x, y=window.bbox.y, w=window.bbox.x + window.bbox.w - split_x, h=window.bbox.h),
        ]
    else:
        columns = [window.bbox]

    regions: list[Window] = []
    for column_index, column_bbox in enumerate(columns):
        horizontal = _split_horizontal_by_gaps(column_bbox, elements)
        for row_index, row_bbox in enumerate(horizontal):
            region_id = _region_id(column_index, row_index, len(columns), len(horizontal))
            regions.append(
                Window(
                    id=region_id,
                    bbox=row_bbox,
                    title=None,
                    z=len(regions) + 1,
                    elements=[],
                )
            )

    for element in elements:
        target = find_containing_window(element.bbox, regions)
        if target is not None:
            target.elements.append(element)

    for region in regions:
        region.title = _guess_window_title(region, scene.ocr_boxes)

    return sorted(regions, key=lambda item: (-item.z, item.bbox.y, item.bbox.x))


def _collect_elements(scene: Scene) -> list[Element]:
    elements: list[Element] = []
    for window in scene.windows:
        elements.extend(window.elements)
    elements.extend(scene.orphan_elements)
    return elements


def _best_vertical_split(
    elements: Iterable[Element],
    window_bbox: BBox,
    scene_width: int,
) -> int | None:
    centers = [element.bbox.x + element.bbox.w // 2 for element in elements]
    if len(centers) < 8:
        return None

    x0, _, x1, _ = window_bbox.as_xyxy()
    best: tuple[float, int] | None = None
    step = max(12, (x1 - x0) // 60)
    for split_x in range(int(x0 + (x1 - x0) * 0.22), int(x0 + (x1 - x0) * 0.78), step):
        left = sum(1 for center in centers if center < split_x)
        right = len(centers) - left
        if left < 5 or right < 5:
            continue
        balance = min(left, right) / max(left, right)
        if best is None or balance > best[0]:
            best = (balance, split_x)

    if best is None or best[0] < 0.3:
        return None
    return best[1]


def _split_horizontal_by_gaps(column_bbox: BBox, elements: Iterable[Element]) -> list[BBox]:
    inside = [
        element
        for element in elements
        if center_in(element.bbox, column_bbox)
    ]
    if len(inside) < 8:
        return [column_bbox]

    spans = sorted((element.bbox.y, element.bbox.y + element.bbox.h) for element in inside)
    gaps: list[tuple[int, int, int]] = []
    for (_, y1), (y2, _) in zip(spans, spans[1:]):
        gap = y2 - y1
        if gap >= max(120, column_bbox.h // 12):
            gaps.append((y1, y2, gap))

    if not gaps:
        return [column_bbox]

    split_y = max(gaps, key=lambda item: item[2])[0]
    _, top_y1 = spans[0]
    bottom_y0, _ = spans[-1]
    if split_y - column_bbox.y < column_bbox.h * 0.12:
        return [column_bbox]
    if column_bbox.y + column_bbox.h - split_y < column_bbox.h * 0.12:
        return [column_bbox]

    return [
        BBox(x=column_bbox.x, y=column_bbox.y, w=column_bbox.w, h=split_y - column_bbox.y),
        BBox(x=column_bbox.x, y=split_y, w=column_bbox.w, h=column_bbox.y + column_bbox.h - split_y),
    ]


def _region_id(column_index: int, row_index: int, columns: int, rows: int) -> str:
    if columns == 1 and rows == 1:
        return "window_0"
    if columns > 1 and rows == 1:
        return "region-left" if column_index == 0 else "region-right"
    if columns == 1 and rows > 1:
        return "region-top" if row_index == 0 else "region-bottom"
    col = "left" if column_index == 0 else "right"
    row = "top" if row_index == 0 else "bottom"
    return f"region-{col}-{row}"


def _guess_window_title(window: Window, ocr_boxes: list[OcrBox]) -> str | None:
    band_h = max(28, int(window.bbox.h * 0.06))
    texts = [
        box.text.strip()
        for box in ocr_boxes
        if box.text.strip()
        and center_in(box.bbox, window.bbox)
        and box.bbox.y <= window.bbox.y + band_h
    ]
    if not texts:
        return None
    merged = " ".join(texts[:4])
    return merged[:64]


def _shift_elements(elements: list[Element], origin: BBox) -> list[Element]:
    shifted: list[Element] = []
    for element in elements:
        bbox = element.bbox
        shifted.append(
            Element(
                id=element.id,
                type=element.type,
                text=element.text,
                bbox=BBox(
                    x=bbox.x - origin.x,
                    y=bbox.y - origin.y,
                    w=bbox.w,
                    h=bbox.h,
                ),
                confidence=element.confidence,
                metadata=dict(element.metadata),
                children=list(element.children),
            )
        )
    return shifted


def _shift_ocr_boxes(boxes: list[OcrBox], origin: BBox) -> list[OcrBox]:
    shifted: list[OcrBox] = []
    for box in boxes:
        bbox = box.bbox
        shifted.append(
            OcrBox(
                text=box.text,
                bbox=BBox(
                    x=bbox.x - origin.x,
                    y=bbox.y - origin.y,
                    w=bbox.w,
                    h=bbox.h,
                ),
                confidence=box.confidence,
                level=box.level,
            )
        )
    return shifted


def _safe_filename(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "window"
