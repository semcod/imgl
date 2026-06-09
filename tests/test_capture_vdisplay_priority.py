"""vdisplay mirror must run before portal on default capture."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from imgl.capture import capture_screen


def test_capture_prefers_vdisplay_over_portal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "screen.png"
    from PIL import Image

    portal = MagicMock(side_effect=AssertionError("portal must not run"))

    def fake_vdisplay(path, **kwargs):
        Image.new("RGB", (80, 60), color=(10, 120, 200)).save(path)
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
        with patch("imgl.capture._capture_with_portal", portal):
            result = capture_screen(out, interactive=False, prefer_mirror=True)

    assert result == out
    portal.assert_not_called()
    assert out.is_file()


def test_capture_interactive_uses_mirror_not_portal(tmp_path: Path) -> None:
    from imgl.control import capture_interactive

    out = tmp_path / "screen.png"
    from PIL import Image

    def fake_vdisplay(path, **kwargs):
        Image.new("RGB", (40, 30), color=(200, 40, 40)).save(path)
        return {"method": "mirror", "path": str(path)}

    fake_host = types.ModuleType("vdisplay.capture.host")
    fake_host.capture_host_to_file = fake_vdisplay
    fake_capture = types.ModuleType("vdisplay.capture")
    fake_capture.host = fake_host

    with patch.dict(
        sys.modules,
        {
            "vdisplay": types.ModuleType("vdisplay"),
            "vdisplay.capture": fake_capture,
            "vdisplay.capture.host": fake_host,
        },
    ):
        result = capture_interactive(out, verify=False, portal=False)

    assert result == out


def test_capture_interactive_portal_fallback_on_wayland(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from imgl.capture import BlankCaptureError
    from imgl.control import capture_interactive

    out = tmp_path / "screen.png"
    monkeypatch.setenv("XDG_SESSION_TYPE", "wayland")
    monkeypatch.setenv("IMGL_CAPTURE_PORTAL_FALLBACK", "1")
    calls: list[bool] = []

    def fake_capture_screen(path, *, interactive=False, **kwargs):
        calls.append(interactive)
        if not interactive:
            raise BlankCaptureError("driver failed")
        from PIL import Image

        Image.new("RGB", (50, 40), color=(30, 180, 90)).save(path)
        return path

    with patch("imgl.control.capture_screen", side_effect=fake_capture_screen):
        with patch("imgl.installs.ensure_vdisplay"):
            result = capture_interactive(out, verify=False, portal=False)

    assert result == out
    assert calls == [False, True]
