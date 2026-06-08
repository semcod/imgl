"""Tests for layout and classification modules."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from imgl.classify.gui_heuristics import classify_scene_elements
from imgl.config import ImglConfig
from imgl.detect.local import DetectedUI, detect_ui_elements
from imgl.geometry import center_in, iou
from imgl.layout import build_windows, extract_window_titles, find_containing_window
from imgl.pipeline import analyze
from imgl.types import BBox, Element, OcrBox, Window


def _font(size: int = 18):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _make_dialog_fixture(path: Path) -> Path:
    """Synthetic settings dialog with label, input frame and button."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (400, 260), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    font = _font()

    # Window body
    draw.rectangle((20, 20, 380, 240), outline=(120, 120, 120), width=2, fill=(250, 250, 250))
    # Title bar band
    draw.rectangle((20, 20, 380, 52), fill=(60, 120, 200))
    draw.text((30, 26), "Settings", fill=(255, 255, 255), font=font)

    # Label + input
    draw.text((40, 90), "Username", fill=(0, 0, 0), font=font)
    draw.rectangle((150, 84, 340, 114), outline=(100, 100, 100), width=1, fill=(255, 255, 255))
    draw.text((158, 90), "tom", fill=(0, 0, 0), font=font)

    # Button
    draw.rectangle((270, 190, 350, 222), outline=(80, 80, 80), width=1, fill=(220, 220, 220))
    draw.text((288, 196), "Save", fill=(0, 0, 0), font=font)

    image.save(path)
    return path


def test_iou_and_center_in():
    a = BBox(x=0, y=0, w=100, h=100)
    b = BBox(x=50, y=50, w=50, h=50)
    assert iou(a, b) > 0
    assert center_in(b, a)
    assert center_in(a, b)  # center of a lies inside b for these overlapping boxes


def test_build_windows_fallback():
    windows = build_windows([], width=800, height=600)
    assert len(windows) == 1
    assert windows[0].id == "win-screen"
    assert windows[0].bbox.w == 800


def test_build_windows_from_panels():
    detected = [
        DetectedUI(id="window_0", role="window", bbox=BBox(x=10, y=10, w=300, h=200), confidence=0.8),
        DetectedUI(id="panel_0", role="panel", bbox=BBox(x=20, y=20, w=100, h=80), confidence=0.6),
    ]
    windows = build_windows(detected, width=400, height=300)
    assert len(windows) == 2
    assert windows[0].z > windows[1].z


def test_find_containing_window():
    outer = Window(id="outer", bbox=BBox(x=0, y=0, w=200, h=200), title=None, z=1)
    inner = Window(id="inner", bbox=BBox(x=20, y=20, w=80, h=80), title=None, z=2)
    box = BBox(x=40, y=40, w=20, h=20)
    match = find_containing_window(box, [outer, inner])
    assert match is not None
    assert match.id == "inner"


def test_extract_window_titles():
    windows = [
        Window(id="win-1", bbox=BBox(x=0, y=0, w=400, h=260), title=None, z=1, elements=[]),
    ]
    detected = [
        DetectedUI(id="titlebar_0", role="titlebar", bbox=BBox(x=0, y=0, w=400, h=40), confidence=0.7),
    ]
    ocr_boxes = [
        OcrBox(text="Settings", bbox=BBox(x=30, y=26, w=80, h=20), confidence=90.0),
    ]
    extract_window_titles(windows, detected, ocr_boxes)
    assert windows[0].title == "Settings"


def test_classify_button_with_geometry():
    window = Window(id="win-1", bbox=BBox(x=0, y=0, w=400, h=300), title=None, z=1, elements=[])
    ocr_boxes = [
        OcrBox(text="Save", bbox=BBox(x=288, y=196, w=40, h=20), confidence=90.0),
    ]
    detected = [
        DetectedUI(
            id="button_0",
            role="button",
            bbox=BBox(x=270, y=190, w=80, h=32),
            confidence=0.68,
        )
    ]
    windows, orphans = classify_scene_elements([window], ocr_boxes, detected, [])
    assert len(orphans) == 0
    types = [element.type for element in windows[0].elements]
    assert "button" in types
    button = next(element for element in windows[0].elements if element.type == "button")
    assert button.text == "Save"


def test_classify_label_input_pair():
    window = Window(id="win-1", bbox=BBox(x=0, y=0, w=400, h=300), title=None, z=1, elements=[])
    ocr_boxes = [
        OcrBox(text="Username", bbox=BBox(x=40, y=90, w=90, h=20), confidence=88.0),
        OcrBox(text="tom", bbox=BBox(x=158, y=90, w=40, h=20), confidence=85.0),
    ]
    input_frame = BBox(x=150, y=84, w=190, h=30)
    windows, orphans = classify_scene_elements([window], ocr_boxes, [], [input_frame])
    types = [element.type for element in windows[0].elements]
    assert "input" in types
    assert "label" in types
    input_el = next(element for element in windows[0].elements if element.type == "input")
    assert input_el.text == "tom"


def test_detect_ui_elements_on_fixture(tmp_path):
    image_path = _make_dialog_fixture(tmp_path / "dialog.png")
    image = Image.open(image_path)
    detected = detect_ui_elements(image)
    roles = {item.role for item in detected}
    assert "titlebar" in roles or "button" in roles or "window" in roles or "panel" in roles


def test_analyze_classifies_dialog(tmp_path):
    image_path = _make_dialog_fixture(tmp_path / "dialog.png")

    mock_boxes = [
        OcrBox(text="Settings", bbox=BBox(x=30, y=26, w=80, h=20), confidence=92.0),
        OcrBox(text="Username", bbox=BBox(x=40, y=90, w=90, h=20), confidence=88.0),
        OcrBox(text="tom", bbox=BBox(x=158, y=90, w=40, h=20), confidence=85.0),
        OcrBox(text="Save", bbox=BBox(x=288, y=196, w=40, h=20), confidence=90.0),
    ]
    mock_backend = MagicMock()
    mock_backend.run.return_value = mock_boxes

    mock_detected = [
        DetectedUI(id="titlebar_0", role="titlebar", bbox=BBox(x=20, y=20, w=360, h=32), confidence=0.7),
        DetectedUI(id="window_0", role="window", bbox=BBox(x=20, y=20, w=360, h=220), confidence=0.8),
        DetectedUI(id="button_0", role="button", bbox=BBox(x=270, y=190, w=80, h=32), confidence=0.68),
    ]

    with (
        patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend),
        patch("imgl.pipeline.detect_ui_merged", return_value=(mock_detected, "mock")),
        patch("imgl.pipeline.detect_input_frames", return_value=[BBox(x=150, y=84, w=190, h=30)]),
    ):
        scene = analyze(image_path, config=ImglConfig(use_img2vql=False))

    assert scene.metadata["detect_source"] == "mock"
    assert len(scene.windows) >= 1
    types = scene.metadata.get("roles", {})
    assert types.get("button", 0) >= 1
    assert types.get("input", 0) >= 1
    assert scene.windows[0].title == "Settings"
