"""Tests for keyboard execution."""

from __future__ import annotations

from imgl.execute import _normalize_keys, execute_action


def test_normalize_keys() -> None:
    assert _normalize_keys("ctrl+enter") == "ctrl+Return"
    assert _normalize_keys("enter") == "Return"


def test_execute_key_dry_run() -> None:
    result = execute_action({"action": "key", "keys": "ctrl+Return"}, dry_run=True)
    assert result.ok
    assert "ctrl+Return" in result.message
