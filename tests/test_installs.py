"""Tests for imgl.installs."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from imgl.installs import (
    ensure_vdisplay,
    install_control,
    install_img2nl,
    install_vdisplay,
    install_vql,
)


def test_install_img2nl_missing_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMG2NL_ROOT", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError, match="img2nl not found"):
        install_img2nl()


def test_install_img2nl_calls_pip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "img2nl"
    repo.mkdir()
    monkeypatch.setenv("IMG2NL_ROOT", str(repo))
    with patch("imgl.installs.subprocess.run") as run:
        install_img2nl()
    assert run.call_count == 1
    cmd = run.call_args[0][0]
    assert "-e" in cmd
    assert "[analyze]" in cmd[-1]


def test_install_vdisplay_calls_pip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "vdisplay"
    repo.mkdir()
    monkeypatch.setenv("VDISPLAY_ROOT", str(repo))
    with patch("imgl.installs.subprocess.run") as run:
        install_vdisplay()
    cmd = run.call_args[0][0]
    assert "[pillow]" in cmd[-1]


def test_install_vql_calls_pip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "vql"
    repo.mkdir()
    monkeypatch.setenv("VQL_ROOT", str(repo))
    with patch("imgl.installs.subprocess.run") as run:
        install_vql()
    cmd = run.call_args[0][0]
    assert str(repo) in cmd[-1]


def test_install_control_calls_pip() -> None:
    with patch("imgl.installs.subprocess.run") as run:
        install_control()
    cmd = run.call_args[0][0]
    assert "nlp2imgl" in " ".join(cmd)


def test_ensure_vdisplay_skips_when_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMGL_AUTO_INSTALL_VDISPLAY", "1")
    with patch("imgl.installs.vdisplay_available", return_value=True):
        with patch("imgl.installs.install_vdisplay") as install:
            assert ensure_vdisplay() is True
    install.assert_not_called()


def test_ensure_vdisplay_auto_installs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMGL_AUTO_INSTALL_VDISPLAY", "1")
    with patch("imgl.installs.vdisplay_available", side_effect=[False, True]):
        with patch("imgl.installs.install_vdisplay") as install:
            assert ensure_vdisplay() is True
    install.assert_called_once()
