"""Tests for capture provenance and VQL integration."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from imgl.capture_provenance import (
    enrich_scene_provenance,
    load_capture_meta,
    save_capture_meta,
)
from imgl.export import scene_to_vql
from imgl.execute import execute_action
from imgl.types import BBox, Element, Scene, Window


def test_save_and_load_capture_meta(tmp_path: Path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    save_capture_meta(png, {"method": "mirror", "display": ":0", "monitor": 1})
    loaded = load_capture_meta(png)
    assert loaded["method"] == "mirror"
    assert loaded["display"] == ":0"


def test_enrich_scene_attaches_capture_meta(tmp_path: Path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    save_capture_meta(png, {"method": "mirror", "display": ":0"})

    scene = Scene(
        width=800,
        height=600,
        source_image=str(png),
        windows=[
            Window(
                id="win-1",
                bbox=BBox(x=0, y=0, w=800, h=600),
                title="App",
                z=1,
                elements=[
                    Element(
                        id="win-1-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=100, y=100, w=80, h=32),
                    )
                ],
            )
        ],
    )
    enriched = enrich_scene_provenance(scene)
    assert enriched.metadata["capture"]["method"] == "mirror"


def test_scene_to_vql_includes_capture_and_relations(tmp_path: Path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    scene = Scene(
        width=400,
        height=300,
        source_image=str(png),
        windows=[
            Window(
                id="win-1",
                bbox=BBox(x=10, y=10, w=380, h=280),
                title="Dialog",
                z=1,
                elements=[
                    Element(
                        id="win-1-button-0",
                        type="button",
                        text="OK",
                        bbox=BBox(x=300, y=240, w=70, h=30),
                    )
                ],
            )
        ],
        metadata={
            "capture": {"method": "mirror", "display": ":0"},
            "window_os": {
                "win-1": {
                    "app_label": "Cursor",
                    "window_id": "0xabc",
                    "vision_iou": 0.8,
                }
            },
        },
    )
    program = scene_to_vql(scene)
    assert program["metadata"]["capture"]["method"] == "mirror"
    assert program["metadata"]["window_os"]["win-1"]["app_label"] == "Cursor"
    assert any(rel["kind"] == "contains" for rel in program["scene"]["relations"])

    windows_layer = next(layer for layer in program["scene"]["layers"] if layer["id"] == "windows")
    window_obj = windows_layer["objects"][0]
    assert window_obj["metadata"]["app_label"] == "Cursor"
    assert window_obj["metadata"]["os_window_id"] == "0xabc"


def test_execute_display_mismatch_warning(tmp_path: Path, monkeypatch) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    save_capture_meta(png, {"method": "mirror", "display": ":99"})
    monkeypatch.setenv("DISPLAY", ":0")

    result = execute_action(
        {"action": "click", "x": 10, "y": 20, "image_path": str(png)},
        dry_run=True,
    )
    assert result.ok
    assert "DISPLAY mismatch" in result.message


def test_execute_display_mismatch_strict(tmp_path: Path, monkeypatch) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    save_capture_meta(png, {"method": "mirror", "display": ":99"})
    monkeypatch.setenv("DISPLAY", ":0")
    monkeypatch.setenv("IMGL_STRICT_DISPLAY", "1")

    result = execute_action(
        {"action": "click", "x": 10, "y": 20, "image_path": str(png)},
        dry_run=False,
    )
    assert not result.ok
    assert result.method == "display-guard"


def test_enrich_scene_correlates_os_windows(tmp_path: Path) -> None:
    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    scene = Scene(
        width=1280,
        height=800,
        source_image=str(png),
        windows=[
            Window(
                id="win-main",
                bbox=BBox(x=0, y=0, w=1280, h=800),
                title="Editor",
                z=1,
            )
        ],
    )
    os_windows = [
        {
            "app_label": "Cursor",
            "window_id": "0x1",
            "x": 0,
            "y": 0,
            "width": 1280,
            "height": 800,
            "monitor_name": "DP-1",
            "nl": "Cursor",
        }
    ]
    with patch("imgl.vdisplay_bridge.vdisplay_available", return_value=True):
        with patch("imgl.vdisplay_bridge.list_os_windows", return_value=os_windows):
            with patch(
                "imgl.vdisplay_bridge.correlate_windows",
                return_value=[
                    {
                        "app_label": "Cursor",
                        "window_id": "0x1",
                        "vision_match": {"id": "win-main"},
                        "vision_iou": 0.9,
                    }
                ],
            ):
                enriched = enrich_scene_provenance(scene)

    assert enriched.metadata["window_os"]["win-main"]["app_label"] == "Cursor"


def test_clear_vql_cache_keeps_capture_meta(tmp_path: Path) -> None:
    from imgl.freshness import clear_vql_cache

    png = tmp_path / "screen.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 64)
    save_capture_meta(png, {"method": "mirror", "display": ":0"})
    (tmp_path / "screen.vql.json").write_text("{}", encoding="utf-8")
    removed = clear_vql_cache(png)
    assert any("screen.vql.json" in p for p in removed)
    assert load_capture_meta(png)["method"] == "mirror"
