"""CLI for nlp2imgl."""

from __future__ import annotations

import argparse
import json

from imgl.autodiag import render_report
from nlp2imgl.control import apply_nl_with_diag, doctor_capture
from nlp2imgl.to_dsl import apply_nl, to_dsl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NL → imgl DSL")
    sub = parser.add_subparsers(dest="cmd", required=True)

    to_dsl_p = sub.add_parser("to-dsl", help="NL to DSL line only")
    to_dsl_p.add_argument("prompt")
    to_dsl_p.add_argument("--image", default="screen.png")
    to_dsl_p.add_argument("--window", default=None)

    apply_p = sub.add_parser("apply", help="NL → DSL → dispatch")
    apply_p.add_argument("prompt")
    apply_p.add_argument("--image", default="screen.png")
    apply_p.add_argument("--window", default=None)
    apply_p.add_argument("--dry-run", action="store_true")
    apply_p.add_argument("--no-diagnose", action="store_true")
    apply_p.add_argument("--llm", action="store_true", help="Vision LLM catalog (OpenRouter)")
    apply_fmt = apply_p.add_mutually_exclusive_group()
    apply_fmt.add_argument("--json", action="store_true", help="Output JSON (default: markdown)")
    apply_fmt.add_argument("--yaml", action="store_true", help="Output YAML (default: markdown)")

    doctor_p = sub.add_parser("doctor", help="Diagnose screenshot (img2nl)")
    doctor_p.add_argument("--image", default=None)
    doctor_p.add_argument("--window", default=None)
    doctor_p.add_argument("--full", action="store_true", help="Include vdisplay + vision windows")
    doctor_p.add_argument("--locale", default="pl")
    doctor_fmt = doctor_p.add_mutually_exclusive_group()
    doctor_fmt.add_argument("--json", action="store_true", help="Output JSON (default: markdown)")
    doctor_fmt.add_argument("--yaml", action="store_true", help="Output YAML (default: markdown)")

    args = parser.parse_args(argv)

    def _fmt(cmd_args: argparse.Namespace) -> str:
        from imgl.autodiag import resolve_cli_output_format

        return resolve_cli_output_format(json_flag=cmd_args.json, yaml_flag=cmd_args.yaml)
    if args.cmd == "to-dsl":
        print(to_dsl(args.prompt, image=args.image, window=args.window))
        return 0

    if args.cmd == "doctor":
        if args.full:
            from imgl.vdisplay_bridge import build_window_control_report
            from nlp2imgl.control import default_image_path

            report = build_window_control_report(
                args.image or str(default_image_path()),
                window=args.window,
                locale=args.locale,
            )
            from imgl.terminal_md import print_report

            fmt = _fmt(args)
            print_report(render_report(report, fmt), fmt)
            capture = report.get("capture") or {}
        else:
            capture = doctor_capture(args.image, locale=args.locale)
            from imgl.terminal_md import print_report

            fmt = _fmt(args)
            print_report(
                render_report({"capture": capture, "verdict": capture.get("verdict")}, fmt),
                fmt,
            )
        return (
            0
            if capture.get("verdict") in {"real_ui", "uncertain"} and capture.get("is_fresh", True)
            else 1
        )

    payload = apply_nl_with_diag(
        args.prompt,
        image=args.image,
        window=args.window,
        execute=not args.dry_run,
        dry_run=args.dry_run,
        with_diagnostics=not args.no_diagnose,
        use_llm=args.llm if args.llm else None,
    )
    fmt = _fmt(args)
    if fmt == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif payload.get("diagnostics"):
        from imgl.terminal_md import print_report

        print_report(render_report(payload["diagnostics"], fmt), fmt)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    checks = (payload.get("diagnostics") or {}).get("checks") or {}
    ok = bool(payload.get("ok")) and not checks.get("blocked_stale_capture")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
