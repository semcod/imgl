"""Tests for window discovery and per-window scoping."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from imgl.catalog import build_interactive_catalog
from imgl.export import write_window_preview_images
from imgl.types import BBox, Element, Scene, Window
from imgl.window_scope import (
    apply_discovered_windows,
    crop_window_image,
    discover_windows,
    export_window_crop,
    format_window_picker,
    get_discovered_window,
    is_monolithic_scene,
    pick_focus_window,
    scene_for_window,
    scope_to_focus_window,
    should_scope_window,
    summarize_windows,
)


def _wide_scene() -> Scene:
    return Scene(
        width=1200,
        height=800,
        source_image="/tmp/desktop.png",
        windows=[
            Window(
                id="window_0",
                bbox=BBox(x=0, y=0, w=1200, h=800),
                title=None,
                z=1,
                elements=[
                    Element(
                        id="left-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=120, y=120, w=80, h=30),
                    ),
                    Element(
                        id="left-input-0",
                        type="input",
                        text="hello",
                        bbox=BBox(x=120, y=180, w=180, h=30),
                    ),
                    *[
                        Element(
                            id=f"left-button-{index}",
                            type="button",
                            text=f"L{index}",
                            bbox=BBox(x=80 + index * 12, y=220 + index, w=60, h=24),
                        )
                        for index in range(1, 8)
                    ],
                    *[
                        Element(
                            id=f"right-button-{index}",
                            type="button",
                            text=f"R{index}",
                            bbox=BBox(x=760 + index * 12, y=120 + index, w=60, h=24),
                        )
                        for index in range(8)
                    ],
                ],
            )
        ],
    )


def test_discover_windows_splits_monolithic_scene():
    scene = _wide_scene()
    assert is_monolithic_scene(scene)
    windows = discover_windows(scene)
    assert len(windows) >= 2
    assert {window.id for window in windows} >= {"region-left", "region-right"}


def test_scene_for_window_shifts_coordinates():
    scene = _wide_scene()
    windows = discover_windows(scene)
    left = get_discovered_window(scene, "region-left")
    assert left is not None
    scoped = scene_for_window(scene, left)
    assert scoped.width == left.bbox.w
    assert scoped.height == left.bbox.h
    assert scoped.windows[0].bbox == BBox(x=0, y=0, w=left.bbox.w, h=left.bbox.h)
    assert scoped.windows[0].elements[0].bbox.x < left.bbox.w


def test_build_catalog_scoped_to_window():
    scene = apply_discovered_windows(_wide_scene())
    catalog = build_interactive_catalog(
        scene,
        image_path="/tmp/desktop.png",
        window_id="region-left",
        include_window_entries=False,
    )
    assert catalog
    assert all(
        opt.window_id in {None, "region-left"} or opt.category != "button"
        for opt in catalog
    )
    assert all(opt.window_id != "region-right" for opt in catalog if opt.window_id)


def test_export_window_crop_and_preview(tmp_path: Path):
    image = tmp_path / "desktop.png"
    Image.new("RGB", (1200, 800), color=(30, 30, 30)).save(image)
    scene = apply_discovered_windows(_wide_scene())
    scene.source_image = str(image)
    windows = discover_windows(scene)
    crop = export_window_crop(image, windows[0], output_dir=tmp_path)
    assert crop.is_file()
    opened = crop_window_image(image, windows[0])
    assert opened.size[0] > 0
    previews = write_window_preview_images(scene, windows, tmp_path, source_image=image)
    assert previews
    assert previews[0].is_file()


def test_stacked_layout_splits_horizontally_not_grid(tmp_path: Path):
    image = tmp_path / "stacked.png"
    # dark gutter band in the middle
    from PIL import ImageDraw

    canvas = Image.new("RGB", (800, 1000), color=(40, 40, 40))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 800, 420), fill=(70, 130, 180))
    draw.rectangle((0, 520, 800, 1000), fill=(180, 90, 60))
    canvas.save(image)

    scene = Scene(
        width=800,
        height=1000,
        source_image=str(image),
        windows=[
            Window(
                id="window_0",
                bbox=BBox(x=0, y=0, w=800, h=1000),
                title=None,
                z=1,
                elements=[
                    *[
                        Element(
                            id=f"top-{index}",
                            type="button",
                            text=f"T{index}",
                            bbox=BBox(x=80 + index * 20, y=80 + index, w=60, h=24),
                        )
                        for index in range(10)
                    ],
                    *[
                        Element(
                            id=f"bot-{index}",
                            type="button",
                            text=f"B{index}",
                            bbox=BBox(x=90 + index * 20, y=700 + index, w=60, h=24),
                        )
                        for index in range(10)
                    ],
                ],
            )
        ],
    )
    windows = discover_windows(scene)
    assert len(windows) == 2
    assert {window.id for window in windows} == {"region-top", "region-bottom"}
    assert all(window.bbox.w == 800 for window in windows)


def test_format_window_picker_lists_regions():
    scene = apply_discovered_windows(_wide_scene())
    summaries = summarize_windows(scene)
    text = format_window_picker(summaries, scene=scene)
    assert "Wykryte okna" in text
    assert "region-left" in text or "region-right" in text


def test_single_monitor_region_bottom_alias():
    scene = Scene(
        width=2560,
        height=1600,
        windows=[
            Window(
                id="window_0",
                bbox=BBox(x=0, y=0, w=2560, h=1600),
                title="Desktop",
                z=1,
                elements=[],
            )
        ],
    )
    assert get_discovered_window(scene, "region-bottom") is scene.windows[0]


def test_pick_focus_window_prefers_interactive_region():
    scene = apply_discovered_windows(_wide_scene())
    summaries = summarize_windows(scene)
    picked = pick_focus_window(summaries)
    assert picked is not None
    assert picked.window.id in {"region-left", "region-right"}


def test_scope_to_focus_window_exports_crop(tmp_path: Path):
    image = tmp_path / "desktop.png"
    Image.new("RGB", (1200, 800), color=(30, 30, 30)).save(image)
    scene = apply_discovered_windows(_wide_scene())
    scene.source_image = str(image)
    scoped = scope_to_focus_window(image, scene, output_path=tmp_path / "scoped.png")
    assert scoped is not None
    out, summary = scoped
    assert out.is_file()
    assert summary.interactive_count >= 1
    assert should_scope_window(scene, summary) is True
