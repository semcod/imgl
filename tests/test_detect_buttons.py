"""Regression tests for button blob detection helpers."""

from __future__ import annotations

from PIL import Image

from imgl.detect.local import (
    _button_confidence,
    _button_from_blob_rect,
    _button_role,
    _detect_buttons,
    _overlaps_seen_button,
    _valid_button_blob_size,
    detect_ui_elements,
)


def test_valid_button_blob_size_filters_extremes() -> None:
    assert _valid_button_blob_size(40, 20) is True
    assert _valid_button_blob_size(1, 20) is False
    assert _valid_button_blob_size(40, 1) is False
    assert _valid_button_blob_size(200, 10) is False


def test_button_role_classifies_icon_vs_button() -> None:
    assert _button_role(1.0, 28, 28) == "icon_button"
    assert _button_role(2.5, 80, 32) == "button"


def test_button_confidence_prefers_typical_toolbar_shape() -> None:
    assert _button_confidence(2.0, 60, 24, image_w=800, image_h=600) == 0.68
    assert _button_confidence(8.0, 60, 8, image_w=800, image_h=600) == 0.45


def test_overlaps_seen_button_dedupes_high_iou() -> None:
    box = (10, 10, 50, 40)
    seen = [(12, 12, 48, 38)]
    assert _overlaps_seen_button(box, seen) is True
    assert _overlaps_seen_button((200, 200, 240, 230), seen) is False


def test_button_from_blob_rect_returns_none_for_invalid_blob() -> None:
    im = Image.new("RGB", (400, 300), color=(240, 240, 240))
    assert (
        _button_from_blob_rect(
            im,
            (0, 0, 1, 40),
            scale=1.0,
            image_w=400,
            image_h=300,
            seen_boxes=[],
            element_index=0,
        )
        is None
    )


def test_detect_buttons_finds_contrast_blob() -> None:
    im = Image.new("RGB", (320, 240), color=(230, 230, 230))
    for x in range(180, 260):
        for y in range(40, 72):
            im.putpixel((x, y), (80, 120, 200))

    buttons = _detect_buttons(im, 320, 240)
    assert buttons
    assert any(item.role in {"button", "icon_button"} for item in buttons)


def test_detect_ui_elements_still_includes_buttons(tmp_path) -> None:
    im = Image.new("RGB", (400, 300), color=(245, 245, 245))
    for x in range(280, 360):
        for y in range(220, 252):
            im.putpixel((x, y), (60, 110, 180))

    detected = detect_ui_elements(im, detect_panels=False)
    roles = {item.role for item in detected}
    assert "button" in roles or "icon_button" in roles
