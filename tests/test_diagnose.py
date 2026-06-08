"""Tests for img2nl content diagnosis."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from imgl.config import ImglConfig
from imgl.diagnose import (
    BlankImageError,
    diagnose_content,
    worth_analyzing,
)
from imgl.pipeline import analyze


def _black_image(path: Path, size: tuple[int, int] = (200, 100)) -> Path:
    Image.new("RGB", size, color=(0, 0, 0)).save(path)
    return path


def _ui_like_image(path: Path) -> Path:
    from PIL import ImageDraw, ImageFont

    image = Image.new("RGB", (400, 200), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except OSError:
        font = ImageFont.load_default()
    draw.rectangle((20, 20, 380, 180), outline=(80, 80, 80), width=2)
    draw.rectangle((250, 140, 350, 170), fill=(200, 200, 200), outline=(0, 0, 0))
    draw.text((270, 148), "Save", fill=(0, 0, 0), font=font)
    draw.text((40, 80), "Username", fill=(0, 0, 0), font=font)
    image.save(path)
    return path


def test_worth_analyzing_blank_scene():
    diag = {
        "ok": True,
        "scene_class": "empty_dark_screen",
        "is_blank": True,
        "recommendation": "skip_blank_capture",
    }
    assert not worth_analyzing(diag)


def test_worth_analyzing_ui_scene():
    diag = {
        "ok": True,
        "scene_class": "ui_with_text",
        "features": {"edges": {"text_likelihood": True}},
        "recommendation": "proceed_with_layout",
    }
    assert worth_analyzing(diag)


def test_diagnose_black_image_fallback(tmp_path):
    path = _black_image(tmp_path / "black.png")
    with patch("imgl.diagnose.img2nl_available", return_value=False):
        diag = diagnose_content(path)
    assert diag["ok"]
    assert not worth_analyzing(diag)
    assert diag.get("is_blank") or diag.get("scene_class") == "empty_dark_screen"


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("img2nl"),
    reason="img2nl not installed",
)
def test_diagnose_with_img2nl_black(tmp_path):
    path = _black_image(tmp_path / "black2.png")
    diag = diagnose_content(path, locale="pl")
    assert diag["ok"]
    assert diag["source"] == "img2nl"
    assert not worth_analyzing(diag)


@pytest.mark.skipif(
    not __import__("importlib").util.find_spec("img2nl"),
    reason="img2nl not installed",
)
def test_diagnose_with_img2nl_ui(tmp_path):
    path = _ui_like_image(tmp_path / "ui.png")
    diag = diagnose_content(path, locale="pl")
    assert diag["ok"]
    assert worth_analyzing(diag)


def test_pipeline_skip_blank_raises(tmp_path):
    path = _black_image(tmp_path / "blank.png")
    mock_diag = {
        "ok": True,
        "is_blank": True,
        "scene_class": "empty_dark_screen",
        "worth_analyzing": False,
        "recommendation": "skip_blank_capture",
        "text": "Pusty ekran",
    }
    with (
        patch("imgl.pipeline.diagnose_content", return_value=mock_diag),
        patch("imgl.pipeline.worth_analyzing", return_value=False),
        pytest.raises(BlankImageError),
    ):
        analyze(path, config=ImglConfig(skip_blank=True))


def test_pipeline_includes_content_metadata(tmp_path):
    path = _ui_like_image(tmp_path / "ui2.png")
    mock_diag = {
        "ok": True,
        "source": "img2nl",
        "is_blank": False,
        "scene_class": "ui_blocks",
        "worth_analyzing": True,
        "recommendation": "proceed_with_layout",
        "text": "UI z blokami",
    }
    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with (
        patch("imgl.pipeline.diagnose_content", return_value=mock_diag),
        patch("imgl.pipeline.worth_analyzing", return_value=True),
        patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend),
    ):
        scene = analyze(path, config=ImglConfig(check_content=True))

    assert "content_check" in scene.metadata
    assert scene.metadata["content_check"]["worth_analyzing"] is True
    assert scene.metadata["content_check"]["scene_class"] == "ui_blocks"


def test_cli_diagnose_command(tmp_path, capsys):
    path = _black_image(tmp_path / "d.png")
    with patch("imgl.diagnose.img2nl_available", return_value=False):
        from imgl.cli import main

        result = main(["diagnose", str(path)])
    assert result == 0
    data = __import__("json").loads(capsys.readouterr().out)
    assert "worth_analyzing" in data
