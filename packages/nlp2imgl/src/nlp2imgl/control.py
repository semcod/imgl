"""NL control with autodiagnostics — doctor + apply_nl_with_diag."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dsl2imgl.result import DslResult
from nlp2imgl.to_dsl import apply_nl, use_llm_enabled


def default_image_path() -> Path:
    for key in ("IMGL_IMAGE", "KORU_IMGL_IMAGE"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser()
    return Path("/tmp/koru-imgl-screen.png")


def default_window() -> str | None:
    for key in ("IMGL_WINDOW", "KORU_IMGL_WINDOW"):
        raw = os.environ.get(key, "region-bottom").strip()
        if raw:
            return raw
    return None


def _result_to_dict(result: DslResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(result, DslResult):
        payload = result.to_dict()
    elif isinstance(result, dict):
        payload = result
    else:
        payload = {"ok": bool(getattr(result, "ok", False)), "output": str(result)}
    return {
        "ok": bool(payload.get("ok")),
        "backend": "imgl",
        "verb": payload.get("verb"),
        "output": payload.get("output"),
        "data": payload.get("data") or {},
        "error": payload.get("error"),
        "command": payload.get("command"),
    }


def doctor_capture(image: str | Path | None = None, *, locale: str = "pl") -> dict[str, Any]:
    from imgl.autodiag import diagnose_capture

    img = str(image) if image else str(default_image_path())
    return diagnose_capture(img, locale=locale)


def apply_nl_with_diag(
    prompt: str,
    *,
    image: str | None = None,
    window: str | None = None,
    execute: bool = True,
    dry_run: bool | None = None,
    with_diagnostics: bool | None = None,
    use_llm: bool | None = None,
    locale: str = "pl",
) -> dict[str, Any]:
    """Run NL through nlp2imgl with optional capture diagnose + execute report."""
    from imgl.autodiag import (
        build_execute_report,
        diagnose_capture,
        diagnostics_enabled,
        should_block_blank_capture,
        should_block_stale_capture,
    )

    effective_dry = dry_run if dry_run is not None else not execute
    do_execute = execute and not effective_dry
    do_diag = diagnostics_enabled() if with_diagnostics is None else with_diagnostics
    img = image or str(default_image_path())
    win = window if window is not None else default_window()

    capture = diagnose_capture(img, locale=locale) if do_diag else {}

    if do_diag and should_block_stale_capture(capture):
        report = build_execute_report(
            prompt=prompt,
            image=img,
            window=win,
            dry_run=effective_dry,
            capture=capture,
            result={
                "ok": False,
                "backend": "imgl",
                "error": capture.get("summary") or "stale screenshot",
            },
        )
        return {
            "ok": False,
            "backend": "imgl",
            "error": report["verdict"],
            "blocked_by": "stale_capture",
            "diagnostics": report,
        }

    if do_diag and should_block_blank_capture(capture) and do_execute:
        report = build_execute_report(
            prompt=prompt,
            image=img,
            window=win,
            dry_run=effective_dry,
            capture=capture,
            result={
                "ok": False,
                "backend": "imgl",
                "error": capture.get("summary") or "blank or unusable capture",
            },
        )
        return {
            "ok": False,
            "backend": "imgl",
            "error": report["verdict"],
            "blocked_by": "capture_diagnose",
            "diagnostics": report,
        }

    result = apply_nl(
        prompt,
        image=img,
        window=win,
        execute=do_execute,
        use_llm=use_llm if use_llm is not None else use_llm_enabled(),
    )
    out = _result_to_dict(result)

    if do_diag:
        out["diagnostics"] = build_execute_report(
            prompt=prompt,
            image=img,
            window=win,
            dry_run=effective_dry,
            capture=capture or diagnose_capture(img, locale=locale),
            result=out,
        )
    return out


__all__ = [
    "apply_nl_with_diag",
    "default_image_path",
    "default_window",
    "doctor_capture",
]
