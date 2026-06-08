"""Tests for scene cache and coordinate scaling."""

from __future__ import annotations

import json
from pathlib import Path

from imgl.config import ImglConfig
from imgl.coords import scale_scene_to_screen
from imgl.scene_cache import (
    load_cached_scene,
    load_or_analyze,
    save_scene_cache,
    scene_cache_path,
)
from imgl.types import BBox, Element, Scene, Window


def test_scale_scene_to_screen_doubles_coords():
    scene = Scene(
        width=1000,
        height=2000,
        windows=[
            Window(
                id="w0",
                bbox=BBox(x=10, y=20, w=100, h=200),
                title="T",
                z=1,
                elements=[
                    Element(
                        id="w0-button-0",
                        type="button",
                        text="OK",
                        bbox=BBox(x=50, y=60, w=40, h=20),
                    )
                ],
            )
        ],
        metadata={"scale": 0.5},
    )
    scaled = scale_scene_to_screen(scene, scale=0.5)
    assert scaled.width == 2000
    assert scaled.height == 4000
    assert scaled.windows[0].bbox.x == 20
    assert scaled.windows[0].elements[0].bbox.w == 80


def test_scene_cache_roundtrip(tmp_path: Path):
    scene = Scene(
        width=400,
        height=300,
        source_image=str(tmp_path / "shot.png"),
        windows=[
            Window(
                id="w0",
                bbox=BBox(x=0, y=0, w=400, h=300),
                title="App",
                z=1,
                elements=[],
            )
        ],
    )
    (tmp_path / "shot.png").write_bytes(b"png")
    vql_file = tmp_path / "layout.vql.json"
    save_scene_cache(scene, vql_file)
    assert scene_cache_path(vql_file).is_file()
    loaded = load_cached_scene(tmp_path / "shot.png", vql_file)
    assert loaded is not None
    assert loaded.width == 400


def test_load_or_analyze_uses_cache(tmp_path: Path, monkeypatch):
    image = tmp_path / "shot.png"
    image.write_bytes(b"x")
    vql_file = tmp_path / "layout.vql.json"
    scene = Scene(
        width=100,
        height=100,
        source_image=str(image.resolve()),
        windows=[],
    )
    save_scene_cache(scene, vql_file)

    def fail_analyze(*_args, **_kwargs):
        raise AssertionError("analyze should not run when cache is fresh")

    monkeypatch.setattr("imgl.scene_cache.analyze", fail_analyze)
    loaded = load_or_analyze(image, vql_file=vql_file, config=ImglConfig())
    assert loaded.width == 100
