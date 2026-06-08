"""Tests for imgl package."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image, ImageDraw, ImageFont

from imgl import BBox, Element, OcrBox, Scene, Window, analyze, scene_from_json, scene_to_json
from imgl.export.json_export import scene_from_json as scene_from_json_direct
from imgl.preprocess import preprocess
from imgl.types import Scene as SceneType


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _make_text_image(path: Path, text: str = "Save") -> Path:
    """Create a simple PNG with text for OCR tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (200, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 20), text, fill=(0, 0, 0), font=font)
    image.save(path)
    return path


def test_import():
    import imgl  # noqa: F401

    assert imgl.__version__ == "0.7.0"


def test_bbox_as_xyxy_and_contains():
    outer = BBox(x=0, y=0, w=100, h=100)
    inner = BBox(x=10, y=10, w=20, h=20)
    assert outer.as_xyxy() == (0, 0, 100, 100)
    assert outer.contains(inner)
    assert not inner.contains(outer)


def test_scene_roundtrip_json():
    scene = Scene(
        width=800,
        height=600,
        source_image="/tmp/screen.png",
        windows=[
            Window(
                id="win-1",
                bbox=BBox(x=0, y=0, w=800, h=600),
                title="Settings",
                z=1,
                elements=[
                    Element(
                        id="el-1",
                        type="button",
                        text="Save",
                        bbox=BBox(x=100, y=200, w=80, h=30),
                        confidence=0.9,
                    )
                ],
            )
        ],
        ocr_boxes=[
            OcrBox(
                text="Save",
                bbox=BBox(x=100, y=200, w=80, h=30),
                confidence=95.0,
            )
        ],
        metadata={"lang": "eng"},
    )

    payload = scene_to_json(scene)
    restored = scene_from_json(payload)

    assert restored.width == 800
    assert restored.height == 600
    assert restored.windows[0].title == "Settings"
    assert restored.windows[0].elements[0].text == "Save"
    assert restored.ocr_boxes[0].text == "Save"

    data = json.loads(payload)
    assert data["version"] == "1.0"
    assert data["scene"]["width"] == 800


def test_scene_from_dict():
    data = {
        "scene": {"width": 100, "height": 50, "source_image": None},
        "windows": [],
        "orphan_elements": [],
        "ocr_boxes": [],
        "metadata": {},
    }
    scene = SceneType.from_dict(data)
    assert scene.width == 100
    assert scene.height == 50


def test_preprocess_resize():
    image = Image.new("RGB", (8000, 4000), color=(128, 128, 128))
    path = FIXTURES_DIR / "large.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)

    result = preprocess(path, max_dim=4000)
    assert max(result.width, result.height) == 4000
    assert result.scale < 1.0


def test_analyze_with_mocked_ocr(tmp_path):
    image_path = _make_text_image(tmp_path / "button.png", "Save")

    mock_boxes = [
        OcrBox(
            text="Save",
            bbox=BBox(x=20, y=20, w=60, h=30),
            confidence=90.0,
            level="word",
        )
    ]

    mock_backend = MagicMock()
    mock_backend.run.return_value = mock_boxes

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.config import ImglConfig

        scene = analyze(image_path, lang="eng", config=ImglConfig(detect_inputs=False))

    assert scene.width > 0
    assert scene.height > 0
    assert len(scene.windows) == 1
    assert len(scene.windows) >= 1
    assert len(scene.windows[0].elements) == 1
    assert scene.windows[0].elements[0].text == "Save"
    assert scene.windows[0].elements[0].type in {"text", "label", "button"}
    assert scene.metadata["ocr_backend"] == "tesseract"
    assert "detect_source" in scene.metadata


@pytest.mark.skipif(
    not Path("/usr/bin/tesseract").exists() and not Path("/usr/local/bin/tesseract").exists(),
    reason="tesseract not installed",
)
def test_analyze_e2e_with_tesseract(tmp_path):
    image_path = _make_text_image(tmp_path / "save_button.png", "Save")
    scene = analyze(image_path, lang="eng")

    assert scene.width == 200
    assert scene.height == 80
    assert len(scene.ocr_boxes) >= 1
    texts = [box.text.lower() for box in scene.ocr_boxes]
    assert any("save" in text for text in texts)


def test_cli_analyze_stdout(tmp_path, capsys):
    image_path = _make_text_image(tmp_path / "cli.png", "OK")

    mock_boxes = [
        OcrBox(text="OK", bbox=BBox(x=10, y=10, w=30, h=20), confidence=88.0)
    ]
    mock_backend = MagicMock()
    mock_backend.run.return_value = mock_boxes

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(["analyze", str(image_path), "--json"])

    assert result == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["version"] == "1.0"
    assert data["windows"][0]["elements"][0]["text"] == "OK"


def test_cli_analyze_output_file(tmp_path):
    image_path = _make_text_image(tmp_path / "out.png", "Cancel")
    out_file = tmp_path / "result.json"

    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(["analyze", str(image_path), "-o", str(out_file)])

    assert result == 0
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["scene"]["width"] == 200
