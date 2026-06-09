"""Tests for capture and path resolution."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from imgl.capture import default_capture_path
from imgl.paths import resolve_image_path, resolve_image_path_optional


def test_resolve_image_path_absolute(tmp_path):
    image = tmp_path / "shot.png"
    image.write_bytes(b"fake")
    resolved = resolve_image_path(image)
    assert resolved == image.resolve()


def test_resolve_image_path_relative(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    image = tmp_path / "shot.png"
    image.write_bytes(b"fake")
    resolved = resolve_image_path(Path("shot.png"))
    assert resolved == image.resolve()


def test_resolve_image_path_not_found(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError, match="Image not found"):
        resolve_image_path("missing.png")


def test_resolve_image_path_optional():
    path, error = resolve_image_path_optional(None)
    assert path is None
    assert "required" in error


def test_cli_missing_image_friendly_error(tmp_path, capsys):
    from imgl.cli import main

    missing = tmp_path / "nope.png"
    result = main(["vql", str(missing), "-o", str(tmp_path / "out.json")])
    assert result == 1
    err = capsys.readouterr().err
    assert "Image not found" in err
    assert "imgl capture" in err


def test_capture_default_path(tmp_path):
    path = default_capture_path(tmp_path / "captures" / "x.png")
    assert path.parent.name == "captures"


def test_cli_vql_aborts_on_blank(tmp_path):
    from imgl.cli import main

    path = tmp_path / "black.png"
    from PIL import Image

    Image.new("RGB", (100, 80), color=(0, 0, 0)).save(path)
    result = main(["vql", str(path), "-o", str(tmp_path / "out.json")])
    assert result == 2


def test_cli_vql_allows_blank_with_flag(tmp_path):
    from unittest.mock import MagicMock, patch

    from imgl.cli import main

    path = tmp_path / "black.png"
    from PIL import Image

    Image.new("RGB", (100, 80), color=(0, 0, 0)).save(path)
    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        result = main(["vql", str(path), "--allow-blank", "-o", str(tmp_path / "out.json")])
    assert result == 0


def test_capture_screen_with_mock_vql(tmp_path, monkeypatch: pytest.MonkeyPatch):
    import sys
    import types

    from imgl.capture import capture_screen

    out = tmp_path / "screen.png"
    mock_info = MagicMock()
    mock_info.path = str(out)

    fake_window = types.ModuleType("vql.adopt.window")
    fake_window.capture_screen = MagicMock(return_value=mock_info)
    fake_adopt = types.ModuleType("vql.adopt")
    fake_adopt.window = fake_window
    fake_vql = types.ModuleType("vql")
    fake_vql.adopt = fake_adopt

    monkeypatch.setenv("IMGL_CAPTURE_ALLOW_VQL", "1")
    with patch.dict(sys.modules, {"vql": fake_vql, "vql.adopt": fake_adopt, "vql.adopt.window": fake_window}):
        result = capture_screen(out)
    assert result == out
