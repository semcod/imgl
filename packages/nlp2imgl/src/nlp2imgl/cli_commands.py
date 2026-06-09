"""Command handlers for the nlp2imgl CLI."""

from __future__ import annotations

import argparse
import json
from typing import Any

from imgl.autodiag import render_report, resolve_cli_output_format
from imgl.terminal_md import print_report
from nlp2imgl.control import apply_nl_with_diag, doctor_capture, default_image_path
from nlp2imgl.to_dsl import to_dsl


def output_format(args: argparse.Namespace) -> str:
    return resolve_cli_output_format(json_flag=args.json, yaml_flag=args.yaml)


def run_to_dsl(args: argparse.Namespace) -> int:
    print(to_dsl(args.prompt, image=args.image, window=args.window))
    return 0


def run_doctor(args: argparse.Namespace) -> int:
    fmt = output_format(args)
    if args.full:
        from imgl.vdisplay_bridge import build_window_control_report

        report = build_window_control_report(
            args.image or str(default_image_path()),
            window=args.window,
            locale=args.locale,
        )
        print_report(render_report(report, fmt), fmt)
        capture = report.get("capture") or {}
    else:
        capture = doctor_capture(args.image, locale=args.locale)
        print_report(
            render_report({"capture": capture, "verdict": capture.get("verdict")}, fmt),
            fmt,
        )
    return (
        0
        if capture.get("verdict") in {"real_ui", "uncertain"} and capture.get("is_fresh", True)
        else 1
    )


def _print_apply_payload(payload: dict[str, Any], fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload.get("diagnostics"):
        print_report(render_report(payload["diagnostics"], fmt), fmt)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def run_apply(args: argparse.Namespace) -> int:
    payload = apply_nl_with_diag(
        args.prompt,
        image=args.image,
        window=args.window,
        execute=not args.dry_run,
        dry_run=args.dry_run,
        with_diagnostics=not args.no_diagnose,
        use_llm=args.llm if args.llm else None,
    )
    _print_apply_payload(payload, output_format(args))
    checks = (payload.get("diagnostics") or {}).get("checks") or {}
    ok = bool(payload.get("ok")) and not checks.get("blocked_stale_capture")
    return 0 if ok else 1
