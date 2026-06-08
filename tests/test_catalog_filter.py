"""Tests for catalog noise filtering."""

from __future__ import annotations

from imgl.catalog import build_interactive_catalog
from imgl.catalog_filter import filter_catalog
from imgl.types import BBox, Element, Scene, Window


def _noisy_scene() -> Scene:
    return Scene(
        width=800,
        height=600,
        windows=[
            Window(
                id="window_0",
                bbox=BBox(x=0, y=0, w=800, h=600),
                title="GitHub",
                z=1,
                elements=[
                    Element(
                        id="window_0-button-0",
                        type="button",
                        text="Follow",
                        bbox=BBox(x=700, y=100, w=80, h=32),
                    ),
                    Element(
                        id="window_0-button-1",
                        type="button",
                        text='import json from pathlib import Path',
                        bbox=BBox(x=50, y=400, w=300, h=24),
                    ),
                    Element(
                        id="window_0-button-2",
                        type="button",
                        text=None,
                        bbox=BBox(x=10, y=10, w=40, h=20),
                    ),
                    Element(
                        id="window_0-input-0",
                        type="input",
                        text="Type / to search",
                        bbox=BBox(x=500, y=20, w=200, h=30),
                        metadata={"label": "search"},
                    ),
                ],
            )
        ],
    )


def test_filter_catalog_drops_code_and_generic():
    scene = _noisy_scene()
    raw = build_interactive_catalog(
        scene,
        image_path="/tmp/screen.png",
        filter_noise=False,
    )
    assert len(raw) >= 4
    filtered = filter_catalog(raw)
    labels = [opt.text or opt.label for opt in filtered]
    assert "Follow" in labels
    assert "Type / to search" in labels
    assert not any("import json" in (t or "") for t in labels)
    assert all(opt.index == i for i, opt in enumerate(filtered, start=1))


def test_build_interactive_catalog_filtered_by_default():
    scene = _noisy_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/screen.png")
    assert len(catalog) <= 4
    assert any(opt.text == "Follow" for opt in catalog)
