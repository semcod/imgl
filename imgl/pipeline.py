"""Main analysis pipeline: screenshot -> Scene."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from imgl.classify import classify_scene_elements
from imgl.config import ImglConfig
from imgl.diagnose import BlankImageError, diagnose_content, worth_analyzing
from imgl.detect.img2vql_bridge import detect_ui_merged
from imgl.detect.rectangles import detect_input_frames
from imgl.layout import build_windows, extract_window_titles
from imgl.ocr import get_ocr_backend
from imgl.preprocess import ImageSource, preprocess
from imgl.types import Scene

ImageInput = Union[str, Path, bytes]


def analyze(
    image: ImageInput,
    *,
    lang: str | None = None,
    config: ImglConfig | None = None,
) -> Scene:
    """Analyze a screenshot and return a semantic layout Scene."""
    cfg = config or ImglConfig()
    if lang is not None:
        cfg.lang = lang

    prepared = preprocess(image, max_dim=cfg.max_dim)

    content_diag: dict | None = None
    if cfg.check_content and prepared.source_path:
        content_diag = diagnose_content(
            prepared.source_path,
            locale=cfg.diagnose_locale,
        )
        if not worth_analyzing(content_diag):
            if cfg.skip_blank:
                raise BlankImageError(
                    content_diag.get("text")
                    or f"Blank or low-content image ({content_diag.get('scene_class', 'unknown')})"
                )

    backend = get_ocr_backend(cfg.ocr_backend)
    ocr_boxes = backend.run(
        prepared.image,
        lang=cfg.lang,
        min_confidence=cfg.min_ocr_confidence,
    )

    detected, detect_source = detect_ui_merged(
        prepared.image,
        source_path=prepared.source_path,
        prefer_img2vql=cfg.use_img2vql,
    )
    input_frames = detect_input_frames(prepared.image) if cfg.detect_inputs else []

    windows = build_windows(detected, width=prepared.width, height=prepared.height)
    extract_window_titles(windows, detected, ocr_boxes)

    windows, orphan_elements = classify_scene_elements(
        windows,
        ocr_boxes,
        detected,
        input_frames,
        label_proximity_px=cfg.label_proximity_px,
    )

    element_count = sum(len(window.elements) for window in windows) + len(orphan_elements)
    roles = _count_roles(windows, orphan_elements)

    return Scene(
        width=prepared.width,
        height=prepared.height,
        source_image=prepared.source_path,
        windows=windows,
        orphan_elements=orphan_elements,
        ocr_boxes=ocr_boxes,
        metadata={
            "ocr_backend": cfg.ocr_backend,
            "lang": cfg.lang,
            "scale": prepared.scale,
            "detect_source": detect_source,
            "element_count": element_count,
            "roles": roles,
            **(_content_metadata(content_diag) if content_diag else {}),
        },
    )


def _content_metadata(diag: dict) -> dict:
    return {
        "content_check": {
            "source": diag.get("source", ""),
            "worth_analyzing": worth_analyzing(diag),
            "is_blank": diag.get("is_blank", False),
            "scene_class": diag.get("scene_class", ""),
            "recommendation": diag.get("recommendation", ""),
            "summary": diag.get("text", ""),
        }
    }


def _count_roles(windows, orphan_elements) -> dict[str, int]:
    counts: dict[str, int] = {}
    for window in windows:
        for element in window.elements:
            counts[element.type] = counts.get(element.type, 0) + 1
    for element in orphan_elements:
        counts[element.type] = counts.get(element.type, 0) + 1
    return counts
