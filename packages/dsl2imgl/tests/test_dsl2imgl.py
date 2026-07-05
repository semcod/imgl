"""Tests for dsl2imgl."""

from __future__ import annotations

import pytest

# dsl2imgl is an optional sub-package (`imgl install control`), not part of
# the root imgl venv by default. A bare import here made the *entire* repo's
# `pytest --collect-only` fail with ModuleNotFoundError before collecting a
# single test. Skip cleanly when it's not installed instead.
pytest.importorskip("dsl2imgl")

from dsl2imgl import dispatch
from dsl2imgl.grammar import parse_line, to_text


def test_health() -> None:
    result = dispatch("HEALTH")
    assert result.ok
    assert result.verb == "HEALTH"


def test_grammar_roundtrip() -> None:
    cmd = parse_line('TYPE "hello" IN "Chat input" IMAGE screen.png WINDOW region-bottom EXECUTE 1')
    assert cmd is not None
    assert cmd["verb"] == "TYPE"
    assert cmd["value"] == "hello"
    text = to_text(cmd)
    assert "TYPE" in text
    assert "hello" in text


def test_key_dry_run() -> None:
    result = dispatch("KEY ctrl+Return EXECUTE 0")
    assert result.ok
    assert result.verb == "KEY"


def test_capture_analyze_flags() -> None:
    cmd = parse_line("CAPTURE OUT screen.png INTERACTIVE ANALYZE LANG eng+pol")
    assert cmd is not None
    assert cmd["verb"] == "CAPTURE"
    assert cmd["out"] == "screen.png"
    assert cmd["interactive"] is True
    assert cmd["analyze"] is True
    assert cmd["lang"] == "eng+pol"
