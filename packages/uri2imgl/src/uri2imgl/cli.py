"""CLI for uri2imgl."""

from __future__ import annotations

import argparse
import json

from dsl2imgl import dispatch
from uri2imgl.decode import uri_to_dsl


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="URI → imgl DSL")
    sub = parser.add_subparsers(dest="cmd", required=True)

    dec = sub.add_parser("decode", help="URI to DSL line")
    dec.add_argument("--uri", required=True)

    run = sub.add_parser("run", help="URI → DSL → dispatch")
    run.add_argument("--uri", required=True)
    run.add_argument("--execute", action="store_true")

    args = parser.parse_args(argv)
    line = uri_to_dsl(args.uri)
    if args.cmd == "decode":
        print(line)
        return 0
    if not args.execute:
        line = line.replace("EXECUTE 1", "EXECUTE 0")
    result = dispatch(line)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
