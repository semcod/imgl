"""Tests for imgl.vdisplay_bridge."""

from __future__ import annotations

from imgl.vdisplay_bridge import (
    correlate_windows,
    suggest_imgl_region,
    vdisplay_available,
)


def test_suggest_imgl_region_bottom() -> None:
    window = {"y": 1200, "height": 300}
    assert suggest_imgl_region(window, screen_height=1600) == "region-bottom"


def test_suggest_imgl_region_top() -> None:
    window = {"y": 40, "height": 400}
    assert suggest_imgl_region(window, screen_height=1600) == "region-top"


def test_correlate_windows_finds_overlap() -> None:
    os_windows = [
        {
            "app_label": "Cursor",
            "window_id": "1",
            "x": 0,
            "y": 800,
            "width": 1200,
            "height": 600,
            "monitor_name": "DP-1",
            "nl": "Cursor window",
        }
    ]
    vision_windows = [
        {
            "id": "region-bottom",
            "title": "region-bottom",
            "bbox": {"x": 0, "y": 780, "w": 1280, "h": 620},
            "source": "imgl_vision",
        }
    ]
    rows = correlate_windows(os_windows, vision_windows, screen_width=2560, screen_height=1600)
    assert len(rows) == 1
    assert rows[0]["vision_match"]["id"] == "region-bottom"
    assert rows[0]["vision_iou"] > 0.5


def test_vdisplay_available_is_bool() -> None:
    assert isinstance(vdisplay_available(), bool)
