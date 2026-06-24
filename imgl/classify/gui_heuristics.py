"""GUI element classification from OCR + geometry."""

from __future__ import annotations

from imgl.detect.local import DetectedUI
from imgl.geometry import bbox_distance, center_in, iou
from imgl.types import BBox, Element, OcrBox, Window

BUTTON_ROLES = {"button", "icon_button"}
LABEL_MAX_WORDS = 6
LABEL_MAX_CHARS = 40
BUTTON_MAX_WORDS = 4


def _process_window_elements(
    window: Window,
    window_ocr: list[tuple[int, OcrBox]],
    geometry_buttons: list[DetectedUI],
    input_frames: list[BBox],
    toolbars: list[DetectedUI],
    used_ocr: set[int],
    label_proximity_px: float,
) -> list[Element]:
    window_buttons = [btn for btn in geometry_buttons if center_in(btn.bbox, window.bbox)]
    window_inputs = [frame for frame in input_frames if center_in(frame, window.bbox)]
    window_toolbars = [bar for bar in toolbars if center_in(bar.bbox, window.bbox)]

    elements: list[Element] = []
    element_id = 0

    for bar in window_toolbars:
        elements.append(Element(
            id=f"{window.id}-toolbar-{element_id}",
            type="toolbar",
            text=bar.label or None,
            bbox=bar.bbox,
            confidence=bar.confidence,
            metadata={"source": bar.metadata.get("source", "detect")},
        ))
        element_id += 1

    for button in window_buttons:
        matched = _match_ocr_to_bbox(button.bbox, window_ocr, used_ocr)
        text = " ".join(box.text for _, box in matched) if matched else None
        for index, _ in matched:
            used_ocr.add(index)
        elements.append(Element(
            id=f"{window.id}-button-{element_id}",
            type="button" if button.role == "button" else "icon_button",
            text=text,
            bbox=button.bbox,
            confidence=button.confidence if text else button.confidence * 0.8,
            metadata={"source": button.metadata.get("source", "detect"), "detected_label": button.label},
        ))
        element_id += 1

    label_candidates = _label_candidates(window_ocr, used_ocr)
    input_elements = _build_inputs(
        window_id=window.id,
        input_frames=window_inputs,
        labels=label_candidates,
        ocr_boxes=window_ocr,
        used_ocr=used_ocr,
        label_proximity_px=label_proximity_px,
        start_id=element_id,
    )
    elements.extend(input_elements)
    element_id += len(input_elements)

    for index, box in window_ocr:
        if index in used_ocr:
            continue
        used_ocr.add(index)
        elements.append(Element(
            id=f"{window.id}-text-{element_id}",
            type=_text_or_label(box),
            text=box.text,
            bbox=box.bbox,
            confidence=_normalize_confidence(box.confidence),
            metadata={"ocr_level": box.level, "source": "ocr"},
        ))
        element_id += 1

    return elements


def classify_scene_elements(
    windows: list[Window],
    ocr_boxes: list[OcrBox],
    detected: list[DetectedUI],
    input_frames: list[BBox],
    *,
    label_proximity_px: float = 40.0,
) -> tuple[list[Window], list[Element]]:
    """
    Classify OCR and geometry into semantic elements per window.

    Returns updated windows and orphan elements.
    """
    geometry_buttons = [item for item in detected if item.role in BUTTON_ROLES]
    toolbars = [item for item in detected if item.role == "toolbar"]

    used_ocr: set[int] = set()
    orphans: list[Element] = []

    for window in windows:
        window_ocr = [
            (index, box)
            for index, box in enumerate(ocr_boxes)
            if index not in used_ocr and center_in(box.bbox, window.bbox)
        ]
        window.elements = _process_window_elements(
            window, window_ocr, geometry_buttons, input_frames, toolbars, used_ocr, label_proximity_px
        )

    for index, box in enumerate(ocr_boxes):
        if index in used_ocr:
            continue
        orphans.append(
            Element(
                id=f"orphan-{index}",
                type=_text_or_label(box),
                text=box.text,
                bbox=box.bbox,
                confidence=_normalize_confidence(box.confidence),
                metadata={"ocr_level": box.level, "source": "ocr"},
            )
        )

    return windows, orphans


def _normalize_confidence(value: float) -> float:
    return value / 100.0 if value > 1 else value


def _word_count(text: str) -> int:
    return len(text.split())


def _text_or_label(box: OcrBox) -> str:
    words = _word_count(box.text)
    if words <= 2 and len(box.text) <= 24 and box.text.endswith(":"):
        return "label"
    if words <= 3 and len(box.text) <= 28 and not box.text.isupper():
        return "label"
    return "text"


def _label_candidates(window_ocr: list[tuple[int, OcrBox]], used_ocr: set[int]) -> list[tuple[int, OcrBox]]:
    labels: list[tuple[int, OcrBox]] = []
    for index, box in window_ocr:
        if index in used_ocr:
            continue
        words = _word_count(box.text)
        if words <= LABEL_MAX_WORDS and len(box.text) <= LABEL_MAX_CHARS:
            labels.append((index, box))
    return labels


def _match_ocr_to_bbox(
    bbox: BBox,
    window_ocr: list[tuple[int, OcrBox]],
    used_ocr: set[int],
    *,
    min_iou: float = 0.15,
) -> list[tuple[int, OcrBox]]:
    matched: list[tuple[int, OcrBox]] = []
    for index, box in window_ocr:
        if index in used_ocr:
            continue
        if center_in(box.bbox, bbox) or iou(box.bbox, bbox) >= min_iou:
            matched.append((index, box))
    return matched


def _nearest_label(
    frame: BBox,
    labels: list[tuple[int, OcrBox]],
    used_ocr: set[int],
    *,
    max_distance: float,
) -> tuple[int, OcrBox] | None:
    best: tuple[int, OcrBox] | None = None
    best_distance = max_distance
    for index, label in labels:
        if index in used_ocr:
            continue
        lx1 = label.bbox.x + label.bbox.w
        ly = label.bbox.y + label.bbox.h / 2
        fx = frame.x
        fy = frame.y + frame.h / 2
        # Label to the left or slightly above
        if lx1 <= frame.x + 8 and abs(ly - fy) <= max(label.bbox.h, frame.h):
            distance = bbox_distance(label.bbox, frame)
        elif label.bbox.y + label.bbox.h <= frame.y + 6:
            distance = bbox_distance(label.bbox, frame)
        else:
            continue
        if distance < best_distance:
            best_distance = distance
            best = (index, label)
    return best


def _ocr_inside_frame(
    frame: BBox,
    window_ocr: list[tuple[int, OcrBox]],
    used_ocr: set[int],
) -> list[tuple[int, OcrBox]]:
    return [
        (index, box)
        for index, box in window_ocr
        if index not in used_ocr and center_in(box.bbox, frame)
    ]


def _build_inputs(
    *,
    window_id: str,
    input_frames: list[BBox],
    labels: list[tuple[int, OcrBox]],
    ocr_boxes: list[tuple[int, OcrBox]],
    used_ocr: set[int],
    label_proximity_px: float,
    start_id: int,
) -> list[Element]:
    elements: list[Element] = []
    element_id = start_id

    for frame in input_frames:
        inside = _ocr_inside_frame(frame, ocr_boxes, used_ocr)
        text = " ".join(box.text for _, box in inside) if inside else None
        for index, _ in inside:
            used_ocr.add(index)

        label_match = _nearest_label(frame, labels, used_ocr, max_distance=label_proximity_px)
        label_text = None
        if label_match:
            label_index, label_box = label_match
            used_ocr.add(label_index)
            label_text = label_box.text
            elements.append(
                Element(
                    id=f"{window_id}-label-{element_id}",
                    type="label",
                    text=label_text,
                    bbox=label_box.bbox,
                    confidence=_normalize_confidence(label_box.confidence),
                    metadata={"source": "ocr", "for_input": f"{window_id}-input-{element_id}"},
                )
            )

        elements.append(
            Element(
                id=f"{window_id}-input-{element_id}",
                type="input",
                text=text,
                bbox=frame,
                confidence=0.65 if text else 0.5,
                metadata={"source": "frame_detect", "label": label_text},
            )
        )
        element_id += 1

    return elements
