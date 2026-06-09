"""CLI for nlp2imgl."""

from __future__ import annotations

from nlp2imgl.cli_commands import run_apply, run_doctor, run_to_dsl
from nlp2imgl.cli_parser import build_parser

_COMMAND_HANDLERS = {
    "to-dsl": run_to_dsl,
    "doctor": run_doctor,
    "apply": run_apply,
}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = _COMMAND_HANDLERS[args.cmd]
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
