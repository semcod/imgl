"""Tests for imgl autodiag + freshness."""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from imgl.autodiag import build_execute_report, diagnose_capture, render_report
from imgl.freshness import capture_sidecar_path, image_freshness, mark_capture_fresh, verify_capture_updated


def test_image_freshness_sidecar(tmp_path: Path) -> None:
    image = tmp_path / "screen.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
    old = image.stat().st_mtime
    os.utime(image, (old - 7200, old - 7200))
    mark_capture_fresh(image)
    fresh = image_freshness(image)
    assert fresh["is_fresh"] is True
    assert fresh["capture_source"] == "sidecar"


def test_verify_capture_updated_fails_on_stale(tmp_path: Path) -> None:
    image = tmp_path / "screen.png"
    image.write_bytes(b"png")
    mtime = image.stat().st_mtime
    with pytest.raises(RuntimeError, match="did not update"):
        verify_capture_updated(image, mtime)


def test_build_execute_report_json() -> None:
    payload = build_execute_report(
        prompt="wpisz test",
        image="/tmp/a.png",
        window="region-bottom",
        dry_run=False,
        capture={"verdict": "real_ui", "is_fresh": True},
        result={
            "ok": True,
            "output": "type 'test' @ (1, 2)",
            "diagnostics": {"verdict": "x"},
            "data": {"execute": {"ok": True, "method": "xdotool", "dry_run": False}},
        },
    )
    js = render_report(payload, "json")
    assert "executed_ok" in js or "real_ui" in js
    assert "diagnostics" not in js


def test_render_report_markdown_uses_yaml_codeblock() -> None:
    payload = build_execute_report(
        prompt="wpisz test",
        image="screen.png",
        window="region-bottom",
        dry_run=False,
        capture={
            "verdict": "blank_capture",
            "is_fresh": True,
            "is_blank": True,
            "path": "screen.png",
            "summary": "Pusty zrzut",
        },
        result={"ok": False, "output": "Pusty zrzut", "data": {}},
    )
    md = render_report(payload, "markdown")
    assert "```yaml" in md
    assert "| Pole |" not in md
    assert "zrzut:" in md
    assert "co_zrobic:" in md
    assert "## Current" in md
    assert "## Next" in md
    assert "```bash" in md
    assert "current:" in md or "Zrzut pusty" in md
    assert "next_cmd:" in md or "imgl capture" in md


def test_pick_output_format_defaults_to_markdown() -> None:
    from imgl.autodiag import pick_output_format

    assert pick_output_format({"capture": {"verdict": "real_ui"}}, "auto") == "markdown"
    assert pick_output_format({}, "auto") == "markdown"
    assert pick_output_format({}, "json") == "json"
    assert pick_output_format({}, "yaml") == "yaml"


def test_build_execute_report_stale_has_current_and_next_cmd() -> None:
    payload = build_execute_report(
        prompt="wpisz test",
        image="/tmp/screen.png",
        window="region-bottom",
        dry_run=True,
        capture={
            "verdict": "stale_capture",
            "is_fresh": False,
            "age_seconds": 125,
            "max_age_seconds": 60,
            "path": "/tmp/screen.png",
            "exists": True,
        },
        result={"ok": False, "error": "stale screenshot", "data": {}},
    )
    assert payload["verdict"] == "stale_capture_error"
    assert "przestarzały" in payload["current"]
    assert "imgl capture --interactive" in payload["next_cmd"]
    assert "/tmp/screen.png" in payload["next_cmd"]


def test_diagnose_capture_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    image = tmp_path / "screen.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
    os.utime(image, (time.time() - 120, time.time() - 120))

    def fake_diag(_path, **_kwargs):
        return {
            "ok": True,
            "width": 100,
            "height": 100,
            "source": "img2nl",
            "features": {"scene": {"scene_class": "general"}},
        }

    monkeypatch.setattr("imgl.diagnose.diagnose_content", fake_diag)
    monkeypatch.setattr("imgl.diagnose.worth_analyzing", lambda _d: True)
    monkeypatch.setattr("imgl.diagnose.content_summary", lambda _d, **_: "ok")

    out = diagnose_capture(image)
    assert out["verdict"] == "stale_capture"
    assert out["is_fresh"] is False


def test_is_valid_png_rejects_empty(tmp_path: Path) -> None:
    from imgl.freshness import is_valid_png, verify_capture_updated

    image = tmp_path / "screen.png"
    image.write_bytes(b"")
    assert is_valid_png(image) is False
    with pytest.raises(RuntimeError, match="invalid PNG"):
        verify_capture_updated(image, 0.0)


def test_vql_cache_path_names() -> None:
    from imgl.freshness import vql_cache_paths

    names = [p.name for p in vql_cache_paths(Path("/tmp/koru-imgl-screen.png"))]
    assert names == ["koru-imgl-screen.vql.imgl.json", "koru-imgl-screen.vql.json"]
