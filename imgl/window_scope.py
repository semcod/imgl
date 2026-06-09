"""Discover application windows on a screenshot and crop per-window regions."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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


def pick_focus_window(
    summaries: list[WindowSummary],
    *,
    window_index: int | None = None,
    window_id: str | None = None,
) -> WindowSummary | None:
    """Pick the most relevant window region for OCR/adopt (most interactive UI)."""
    if not summaries:
        return None

    if window_id:
        ref = str(window_id).strip().casefold()
        for item in summaries:
            if item.window.id.casefold() == ref:
                return item
            title = (item.window.title or "").casefold()
            if title and title == ref:
                return item
        return None

    if window_index is not None:
        if 1 <= window_index <= len(summaries):
            return summaries[window_index - 1]
        return None

    if len(summaries) == 1:
        return summaries[0]

    return max(
        summaries,
        key=lambda item: (
            item.interactive_count,
            item.element_count,
            item.window.bbox.w * item.window.bbox.h,
        ),
    )


def should_scope_window(scene: Scene, summary: WindowSummary) -> bool:
    """Return True when cropping to the window likely reduces OCR noise."""
    windows = discover_windows(scene)
    if len(windows) > 1:
        return True
    total = max(1, scene.width * scene.height)
    area = summary.window.bbox.w * summary.window.bbox.h
    return area / total < 0.92


def scope_to_focus_window(
    image_path: str | Path,
    scene: Scene,
    *,
    window_index: int | None = None,
    window_id: str | None = None,
    output_path: str | Path | None = None,
) -> tuple[Path, WindowSummary] | None:
    """Crop screenshot to a discovered window region."""
    summaries = summarize_windows(scene, image_path=str(image_path))
    picked = pick_focus_window(
        summaries,
        window_index=window_index,
        window_id=window_id,
    )
    if picked is None or not should_scope_window(scene, picked):
        return None

    source = Path(resolve_image_path(image_path))
    if output_path:
        out = Path(output_path).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        safe_id = _safe_filename(picked.window.id)
        out = source.with_name(f"{source.stem}.{safe_id}{source.suffix or '.png'}")

    crop_window_image(source, picked.window).save(out, format="PNG")
    return out.resolve(), picked


def scope_image_to_focus_window(
    image_path: str | Path,
    *,
    lang: str = "eng+pol",
    window_index: int | None = None,
    window_id: str | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Analyze screenshot, pick focus window, export crop PNG."""
    from imgl.config import ImglConfig
    from imgl.pipeline import analyze

    cfg = ImglConfig()
    cfg.lang = lang
    scene = analyze(image_path, config=cfg)
    scene = apply_discovered_windows(scene)
    scoped = scope_to_focus_window(
        image_path,
        scene,
        window_index=window_index,
        window_id=window_id,
        output_path=output_path,
    )
    if scoped is None:
        return {
            "ok": False,
            "skipped": True,
            "reason": "scope_not_needed",
            "source_image": str(Path(image_path).expanduser()),
        }

    out, summary = scoped
    return {
        "ok": True,
        "skipped": False,
        "path": str(out),
        "source_image": str(Path(image_path).expanduser()),
        "window_id": summary.window.id,
        "window_title": summary.window.title,
        "interactive_count": summary.interactive_count,
        "element_count": summary.element_count,
        "window_count": len(discover_windows(scene)),
    }


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


_SINGLE_WINDOW_ALIASES = frozenset(
    {
        "window_0",
        "region-top",
        "region-bottom",
        "region-left",
        "region-right",
        "region-middle",
    }
)


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
    # Jedno okno (np. 2560×1600): region-bottom/top to alias window_0
    if len(windows) == 1 and ref in _SINGLE_WINDOW_ALIASES:
        return windows[0]
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

    region_boxes: list[BBox]
    layout = _detect_layout_mode(elements, window.bbox)
    if layout == "side_by_side":
        region_boxes = _split_side_by_side(window.bbox, elements)
    else:
        region_boxes = _split_stacked(
            window.bbox,
            elements,
            image_path=scene.source_image,
        )

    regions = [
        Window(
            id=_region_id_for_boxes(index, len(region_boxes), layout),
            bbox=box,
            title=None,
            z=len(region_boxes) - index,
            elements=[],
        )
        for index, box in enumerate(region_boxes)
    ]

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


def _detect_layout_mode(elements: Iterable[Element], window_bbox: BBox) -> str:
    """Return 'side_by_side' or 'stacked' based on element x-cluster separation."""
    items = list(elements)
    if len(items) < 8:
        return "stacked"

    x0, _, x1, _ = window_bbox.as_xyxy()
    width = max(1, x1 - x0)
    mid = x0 + width // 2
    left = [element for element in items if element.bbox.x + element.bbox.w // 2 < mid]
    right = [element for element in items if element.bbox.x + element.bbox.w // 2 >= mid]
    if len(left) < 8 or len(right) < 8:
        return "stacked"

    left_max = max(element.bbox.x + element.bbox.w for element in left)
    right_min = min(element.bbox.x for element in right)
    gap = right_min - left_max
    balance = min(len(left), len(right)) / max(len(left), len(right))
    if gap >= max(50, int(width * 0.02)) and balance >= 0.3:
        return "side_by_side"
    return "stacked"


def _split_side_by_side(window_bbox: BBox, elements: Iterable[Element]) -> list[BBox]:
    split_x = _best_vertical_split(elements, window_bbox)
    if split_x is None:
        return [window_bbox]
    x0, y0, x1, y1 = window_bbox.as_xyxy()
    return [
        BBox(x=x0, y=y0, w=split_x - x0, h=y1 - y0),
        BBox(x=split_x, y=y0, w=x1 - split_x, h=y1 - y0),
    ]


def _split_stacked(
    window_bbox: BBox,
    elements: Iterable[Element],
    *,
    image_path: str | None,
) -> list[BBox]:
    items = [element for element in elements if center_in(element.bbox, window_bbox)]
    candidates = _element_gap_gutters(window_bbox, items)
    if image_path and Path(image_path).is_file():
        candidates.extend(_image_gutter_candidates(image_path, window_bbox))
    boxes = _regions_from_balanced_gutters(window_bbox, items, candidates)
    if boxes:
        return boxes
    return _split_by_element_y_gaps(window_bbox, items)


def _image_gutter_candidates(image_path: str, window_bbox: BBox) -> list[tuple[int, int, int]]:
    """Find dark/uniform horizontal bands that separate stacked windows."""
    image = Image.open(resolve_image_path(image_path)).convert("L")
    x0, y0, x1, y1 = window_bbox.as_xyxy()
    width = max(1, x1 - x0)
    height = max(1, y1 - y0)
    step_y = max(3, height // 600)
    step_x = max(3, width // 80)

    gutters: list[tuple[int, int, int]] = []
    run_start: int | None = None
    run_end: int | None = None

    for y in range(y0, y1, step_y):
        samples = [
            image.getpixel((x, min(y, y1 - 1)))
            for x in range(x0, x1, step_x)
        ]
        if not samples:
            continue
        if statistics.pstdev(samples) <= 9:
            if run_start is None:
                run_start = y
            run_end = y
            continue
        if run_start is not None and run_end is not None:
            gutters.append((run_start, run_end + step_y, run_end + step_y - run_start))
        run_start = None
        run_end = None

    if run_start is not None and run_end is not None:
        gutters.append((run_start, run_end + step_y, run_end + step_y - run_start))

    min_gutter = max(40, int(height * 0.03))
    min_region = max(120, int(height * 0.1))
    return [
        gutter
        for gutter in gutters
        if gutter[2] >= min_gutter
        and gutter[0] - y0 >= min_region
        and y1 - gutter[1] >= min_region
    ]


def _element_gap_gutters(window_bbox: BBox, elements: list[Element]) -> list[tuple[int, int, int]]:
    if len(elements) < 8:
        return []
    spans = sorted((element.bbox.y, element.bbox.y + element.bbox.h) for element in elements)
    x0, y0, x1, y1 = window_bbox.as_xyxy()
    min_gap = max(120, int(window_bbox.h * 0.05))
    gutters: list[tuple[int, int, int]] = []
    for (_, y1_span), (y2_span, _) in zip(spans, spans[1:]):
        gap = y2_span - y1_span
        if gap < min_gap:
            continue
        start = max(y0, y1_span)
        end = min(y1, y2_span)
        if end - start >= min_gap // 2:
            gutters.append((start, end, end - start))
    return gutters


def _regions_from_balanced_gutters(
    window_bbox: BBox,
    elements: list[Element],
    candidates: list[tuple[int, int, int]],
) -> list[BBox]:
    if not candidates:
        return []

    x0, y0, x1, y1 = window_bbox.as_xyxy()
    width = x1 - x0
    min_region = max(120, int(window_bbox.h * 0.1))

    scored: list[tuple[float, tuple[int, int, int]]] = []
    for gutter_start, gutter_end, _ in candidates:
        above = sum(
            1
            for element in elements
            if element.bbox.y + element.bbox.h // 2 < gutter_start
        )
        below = sum(
            1
            for element in elements
            if element.bbox.y + element.bbox.h // 2 > gutter_end
        )
        if above < 8 or below < 8:
            continue
        balance = min(above, below) / max(above, below)
        if balance < 0.18:
            continue
        if gutter_start - y0 < min_region or y1 - gutter_end < min_region:
            continue
        scored.append((balance, (gutter_start, gutter_end, gutter_end - gutter_start)))

    if not scored:
        return []

    scored.sort(key=lambda item: item[0], reverse=True)
    chosen = [item[1] for item in scored[:2]]
    chosen.sort(key=lambda item: item[0])

    bounds = [y0]
    for gutter_start, gutter_end, _ in chosen:
        bounds.extend([gutter_start, gutter_end])
    bounds.append(y1)

    boxes: list[BBox] = []
    for index in range(0, len(bounds) - 1, 2):
        top = bounds[index]
        bottom = bounds[index + 1]
        if bottom - top < min_region:
            continue
        boxes.append(BBox(x=x0, y=top, w=width, h=bottom - top))
    return boxes if len(boxes) >= 2 else []


def _split_by_element_y_gaps(window_bbox: BBox, elements: Iterable[Element]) -> list[BBox]:
    inside = [element for element in elements if center_in(element.bbox, window_bbox)]
    if len(inside) < 8:
        return [window_bbox]

    spans = sorted((element.bbox.y, element.bbox.y + element.bbox.h) for element in inside)
    gaps: list[tuple[int, int, int]] = []
    for (_, y1), (y2, _) in zip(spans, spans[1:]):
        gap = y2 - y1
        if gap >= max(160, window_bbox.h // 8):
            gaps.append((y1, y2, gap))
    if not gaps:
        return [window_bbox]

    split_y = max(gaps, key=lambda item: item[2])[1]
    x0, y0, x1, y1 = window_bbox.as_xyxy()
    min_region = max(120, int(window_bbox.h * 0.1))
    if split_y - y0 < min_region or y1 - split_y < min_region:
        return [window_bbox]
    return [
        BBox(x=x0, y=y0, w=x1 - x0, h=split_y - y0),
        BBox(x=x0, y=split_y, w=x1 - x0, h=y1 - split_y),
    ]


def _best_vertical_split(elements: Iterable[Element], window_bbox: BBox) -> int | None:
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


def _region_id_for_boxes(index: int, count: int, layout: str) -> str:
    if count == 1:
        return "window_0"
    if layout == "side_by_side":
        return "region-left" if index == 0 else "region-right"
    if count == 2:
        return "region-top" if index == 0 else "region-bottom"
    if count == 3:
        return ("region-top", "region-middle", "region-bottom")[index]
    return f"region-{index + 1}"


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
