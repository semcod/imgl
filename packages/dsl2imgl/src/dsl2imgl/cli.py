"""CLI for dsl2imgl."""

from __future__ import annotations

import argparse
import json
import sys

from dsl2imgl import dispatch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="imgl control DSL bus")
    sub = parser.add_subparsers(dest="cmd")

    exec_p = sub.add_parser("exec", help="Execute one DSL line")
    exec_p.add_argument("line", help='e.g. ACTIONS screen.png WINDOW region-bottom LLM')

    sub.add_parser("health", help="HEALTH check")

    legacy = argparse.ArgumentParser(add_help=False)
    legacy.add_argument("-c", "--command", dest="line")
    legacy.add_argument("script", nargs="?", default="")

    args, rest = parser.parse_known_args(argv)
    if args.cmd == "exec":
        result = dispatch(args.line)
        print(result.to_json())
        return 0 if result.ok else 1
    if args.cmd == "health":
        result = dispatch("HEALTH")
        print(result.to_json())
        return 0

    if rest or (hasattr(args, "line") and args.line):
        line = getattr(args, "line", None) or " ".join(rest)
        result = dispatch(line)
        print(result.to_json())
        return 0 if result.ok else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
