"""Tests for HTML and SVG export."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from imgl.export import scene_to_html, scene_to_svg
from imgl.types import BBox, Element, Scene, Window


def _make_dialog_fixture(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (400, 260), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle((20, 20, 380, 240), outline=(120, 120, 120), width=2, fill=(250, 250, 250))
    draw.rectangle((270, 190, 350, 222), outline=(80, 80, 80), width=1, fill=(220, 220, 220))
    draw.text((288, 196), "Save", fill=(0, 0, 0), font=font)
    image.save(path)
    return path


def _sample_scene() -> Scene:
    return Scene(
        width=400,
        height=260,
        source_image="/tmp/dialog.png",
        windows=[
            Window(
                id="win-1",
                bbox=BBox(x=20, y=20, w=360, h=220),
                title="Settings",
                z=2,
                elements=[
                    Element(
                        id="win-1-label-0",
                        type="label",
                        text="Username",
                        bbox=BBox(x=40, y=90, w=90, h=20),
                        confidence=0.88,
                        metadata={"for_input": "win-1-input-0"},
                    ),
                    Element(
                        id="win-1-input-0",
                        type="input",
                        text="tom",
                        bbox=BBox(x=150, y=84, w=190, h=30),
                        confidence=0.65,
                        metadata={"label": "Username"},
                    ),
                    Element(
                        id="win-1-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=270, y=190, w=80, h=32),
                        confidence=0.68,
                    ),
                ],
            )
        ],
        orphan_elements=[
            Element(
                id="orphan-0",
                type="text",
                text="Desktop",
                bbox=BBox(x=5, y=5, w=60, h=16),
                confidence=0.7,
            )
        ],
        metadata={"detect_source": "test"},
    )


def test_scene_to_html_structure():
    html = scene_to_html(_sample_scene())
    assert "<!DOCTYPE html>" in html
    assert 'class="scene"' in html
    assert 'role="window"' in html
    assert 'data-id="win-1"' in html
    assert 'data-type="button"' in html
    assert 'data-text="Save"' in html
    assert 'data-type="input"' in html
    assert 'value="tom"' in html
    assert "Settings" in html
    assert "Username" in html


def test_scene_to_html_embed_image():
    html = scene_to_html(_sample_scene(), embed_image=True)
    assert 'class="scene-bg"' in html
    assert 'src="/tmp/dialog.png"' in html


def test_scene_to_html_escapes_special_chars():
    scene = Scene(
        width=100,
        height=50,
        windows=[
            Window(
                id="win-x",
                bbox=BBox(x=0, y=0, w=100, h=50),
                title='A <script> & "test"',
                z=1,
                elements=[
                    Element(
                        id="el-1",
                        type="text",
                        text="<unsafe>",
                        bbox=BBox(x=5, y=5, w=40, h=20),
                    )
                ],
            )
        ],
    )
    html = scene_to_html(scene)
    assert "<script>" not in html
    assert "&lt;unsafe&gt;" in html
    assert "&lt;script&gt;" in html


def test_scene_to_svg_wireframe():
    svg = scene_to_svg(_sample_scene(), mode="wireframe")
    assert svg.startswith('<?xml version="1.0"')
    assert 'width="400"' in svg
    assert 'data-type="button"' in svg
    assert ">Save</text>" in svg
    assert 'class="window"' in svg
    assert "<image" not in svg


def test_scene_to_svg_overlay():
    svg = scene_to_svg(
        _sample_scene(),
        mode="overlay",
        background="/tmp/dialog.png",
    )
    assert '<image href="/tmp/dialog.png"' in svg
    assert 'data-type="input"' in svg


def test_scene_to_svg_invalid_mode():
    with pytest.raises(ValueError, match="Unknown SVG mode"):
        scene_to_svg(_sample_scene(), mode="invalid")


def test_cli_html_command(tmp_path, capsys):
    image_path = _make_dialog_fixture(tmp_path / "dialog.png")
    from imgl.types import OcrBox

    mock_boxes = [
        OcrBox(text="Save", bbox=BBox(x=288, y=196, w=40, h=20), confidence=90.0),
    ]
    mock_backend = MagicMock()
    mock_backend.run.return_value = mock_boxes

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(["html", str(image_path)])

    assert result == 0
    output = capsys.readouterr().out
    assert "<!DOCTYPE html>" in output
    assert 'data-type="button"' in output or 'class="scene"' in output


def test_cli_svg_command_writes_file(tmp_path):
    image_path = _make_dialog_fixture(tmp_path / "dialog.png")
    out_file = tmp_path / "scene.svg"

    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(
            [
                "svg",
                str(image_path),
                "--mode",
                "overlay",
                "-o",
                str(out_file),
            ]
        )

    assert result == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert content.startswith("<?xml")
    assert "<image" in content


def test_cli_svg_wireframe_default(tmp_path, capsys):
    from PIL import Image

    image_path = tmp_path / "blank.png"
    Image.new("RGB", (100, 80), color=(255, 255, 255)).save(image_path)

    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(["svg", str(image_path)])

    assert result == 0
    assert "<?xml" in capsys.readouterr().out
