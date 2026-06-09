"""Tests for terminal markdown colorization."""

from __future__ import annotations

from imgl.autodiag import build_execute_report, render_report
from imgl.terminal_md import colorize_markdown, stdout_color_enabled


def test_stdout_color_disabled_with_no_color(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    assert stdout_color_enabled() is False


def test_colorize_markdown_adds_ansi_when_forced() -> None:
    payload = build_execute_report(
        prompt="wpisz test",
        image="/tmp/screen.png",
        window="region-bottom",
        dry_run=True,
        capture={
            "verdict": "stale_capture",
            "is_fresh": False,
            "age_seconds": 90,
            "max_age_seconds": 60,
            "path": "/tmp/screen.png",
            "exists": True,
        },
        result={"ok": False, "error": "stale", "data": {}},
    )
    md = render_report(payload, "markdown")
    colored = colorize_markdown(md, enabled=True)
    assert "\033[" in colored
    assert "## Current" in colored or "Current" in colored
    assert "imgl capture" in colored
    assert "stale_capture_error" in colored


def test_colorize_markdown_plain_when_disabled() -> None:
    text = "# imgl — autodiagnostyka\n\n**Werdykt:** `planned_ok`\n"
    assert colorize_markdown(text, enabled=False) == text


def test_resolve_cli_output_format_flags() -> None:
    from imgl.autodiag import resolve_cli_output_format

    assert resolve_cli_output_format() == "markdown"
    assert resolve_cli_output_format(json_flag=True) == "json"
    assert resolve_cli_output_format(yaml_flag=True) == "yaml"
