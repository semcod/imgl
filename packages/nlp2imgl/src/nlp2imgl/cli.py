"""CLI for nlp2imgl."""

from __future__ import annotations

import argparse
import json

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

    args = parser.parse_args(argv)
    if args.cmd == "to-dsl":
        print(to_dsl(args.prompt, image=args.image, window=args.window))
        return 0
    result = apply_nl(
        args.prompt,
        image=args.image,
        window=args.window,
        execute=not args.dry_run,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
