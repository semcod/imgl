"""Argparse setup for the nlp2imgl CLI."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
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

    return parser
