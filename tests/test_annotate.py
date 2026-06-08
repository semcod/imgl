"""Tests for numbered overlay export."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from imgl.catalog import build_interactive_catalog
from imgl.export import default_annotated_path, write_annotated_image
from imgl.nlp2uri import prompt_to_imgl_uri
from imgl.types import BBox, Element, Scene, Window


def _scene() -> Scene:
    return Scene(
        width=400,
        height=260,
        source_image="/tmp/dialog.png",
        windows=[
            Window(
                id="win-settings",
                bbox=BBox(x=20, y=20, w=360, h=220),
                title="Settings",
                z=2,
                elements=[
                    Element(
                        id="win-settings-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=270, y=190, w=80, h=32),
                    ),
                ],
            )
        ],
    )


def test_default_annotated_path():
    assert default_annotated_path("/tmp/screen.png") == Path("/tmp/screen.numbered.png")


def test_write_annotated_image(tmp_path: Path):
    image = tmp_path / "shot.png"
    Image.new("RGB", (400, 260), color=(240, 240, 240)).save(image)
    scene = _scene()
    scene.source_image = str(image)
    catalog = build_interactive_catalog(scene, image_path=str(image))
    out = tmp_path / "shot.numbered.png"
    path = write_annotated_image(scene, catalog, out, source_image=image)
    assert path.is_file()
    assert path.stat().st_size > 100


def test_nlp2uri_mapa():
    resolved = prompt_to_imgl_uri("pokaż mapę numerów", image="/tmp/screen.png")
    assert resolved is not None
    assert "action=annotate" in resolved.uri
