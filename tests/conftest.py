"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_vdisplay_auto_install(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests mock vdisplay; never pip-install during unit tests."""
    monkeypatch.setenv("IMGL_AUTO_INSTALL_VDISPLAY", "0")
