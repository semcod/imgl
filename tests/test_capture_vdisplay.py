"""Tests for vdisplay-first capture."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import patch

from imgl.capture import capture_screen


def test_capture_screen_prefers_vdisplay(tmp_path: Path) -> None:
    out = tmp_path / "screen.png"
    from PIL import Image

    def fake_vdisplay(path, **kwargs):
        Image.new("RGB", (40, 30), color=(200, 40, 40)).save(path)
        return {"method": "mirror", "path": str(path)}

    fake_host = types.ModuleType("vdisplay.capture.host")
    fake_host.capture_host_to_file = fake_vdisplay
    fake_capture = types.ModuleType("vdisplay.capture")
    fake_capture.host = fake_host
    fake_vdisplay_mod = types.ModuleType("vdisplay")
    fake_vdisplay_mod.capture = fake_capture

    with patch.dict(
        sys.modules,
        {
            "vdisplay": fake_vdisplay_mod,
            "vdisplay.capture": fake_capture,
            "vdisplay.capture.host": fake_host,
        },
    ):
        result = capture_screen(out, monitor=1)

    assert result == out
    assert out.is_file()
