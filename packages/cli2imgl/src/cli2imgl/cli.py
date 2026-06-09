"""REPL for imgl control DSL and NL."""

from __future__ import annotations

import json
import sys

from dsl2imgl import dispatch
from nlp2imgl.to_dsl import apply_nl, to_dsl


def main(argv: list[str] | None = None) -> int:
    del argv
    print("cli2imgl — wpisz DSL lub NL (quit)")
    while True:
        try:
            line = input("imgl> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line or line.lower() in {"quit", "exit"}:
            return 0
        if line.upper().split()[0] in {
            "HEALTH", "CAPTURE", "ANALYZE", "ACTIONS", "RESOLVE", "CLICK", "TYPE", "KEY", "EXECUTE",
        }:
            result = dispatch(line)
        else:
            print(f"DSL: {to_dsl(line)}")
            result = apply_nl(line)
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
