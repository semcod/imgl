"""Tests for dsl2imgl."""

from __future__ import annotations

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
