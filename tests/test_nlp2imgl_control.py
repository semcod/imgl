"""Tests for nlp2imgl.control (requires install-control)."""

from __future__ import annotations

import pytest

nlp2imgl = pytest.importorskip("nlp2imgl.control")
apply_nl_with_diag = nlp2imgl.apply_nl_with_diag


def test_apply_nl_with_diag_blocks_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KORU_IMGL_STALE_BLOCK", "1")

    def fake_diag(_path, **_kwargs):
        return {
            "ok": False,
            "verdict": "stale_capture",
            "is_fresh": False,
            "summary": "stary zrzut",
        }

    monkeypatch.setattr("imgl.autodiag.diagnose_capture", fake_diag)
    monkeypatch.setattr(
        "nlp2imgl.control.apply_nl",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not run")),
    )

    out = apply_nl_with_diag(
        "wpisz test",
        image="/tmp/koru-imgl-screen.png",
        execute=True,
        with_diagnostics=True,
    )
    assert out["ok"] is False
    assert out["blocked_by"] == "stale_capture"
