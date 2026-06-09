"""CQRS bus — single dispatch entry for imgl DSL."""

from __future__ import annotations

import json
from typing import Any

from dsl2imgl.codec import envelope_from_bytes, envelope_from_json, parse_text
from dsl2imgl.events import EventStore
from dsl2imgl.grammar import to_text
from dsl2imgl.handlers.runtime import (
    handle_actions,
    handle_analyze,
    handle_capture,
    handle_execute,
    handle_health,
    handle_resolve,
)
from dsl2imgl.result import DslResult
from dsl2imgl.schema_registry import COMMAND_VERBS, QUERY_VERBS

_HANDLERS = {
    "HEALTH": handle_health,
    "CAPTURE": handle_capture,
    "ANALYZE": handle_analyze,
    "ACTIONS": handle_actions,
    "RESOLVE": handle_resolve,
    "CLICK": handle_execute,
    "TYPE": handle_execute,
    "KEY": handle_execute,
    "EXECUTE": handle_execute,
    "AGENT": handle_execute,
}


def _run_handler(payload: dict[str, Any], *, line: str) -> DslResult:
    verb = str(payload.get("verb", "")).upper()
    handler = _HANDLERS.get(verb)
    if handler is None:
        return DslResult(ok=False, verb=verb, command=line, error=f"unknown verb: {verb}")
    result = handler(payload)
    result.verb = verb
    result.command = line
    result.action = verb.lower()
    return result


def dispatch(
    envelope: str | dict[str, Any] | bytes,
    *,
    default_file: str | None = None,
    correlation_id: str = "",
) -> DslResult:
    raw_line = ""
    try:
        if isinstance(envelope, bytes):
            payload = envelope_from_bytes(envelope)
            raw_line = to_text(payload)
        elif isinstance(envelope, dict):
            from dsl2imgl.codec import validate_payload

            payload = validate_payload(envelope)
            raw_line = to_text(payload)
        else:
            raw_line = str(envelope).strip()
            if not raw_line or raw_line.startswith("#"):
                return DslResult(ok=True, command=raw_line, action="noop")
            payload = parse_text(raw_line)
            if not payload:
                return DslResult(ok=True, command=raw_line, action="noop")

        verb = str(payload["verb"]).upper()
        result = _run_handler(payload, line=raw_line)

        if verb in COMMAND_VERBS and result.ok:
            store = EventStore.for_default(default_file)
            event_id = store.append_command(payload, result.to_dict(), correlation_id=correlation_id)
            result.event_id = event_id

        return result
    except Exception as exc:
        return DslResult(ok=False, command=raw_line or str(envelope), error=str(exc))


def execute_dsl_line(line: str, *, default_file: str | None = None) -> DslResult:
    return dispatch(line, default_file=default_file)


def execute_dsl(text: str, *, default_file: str | None = None) -> list[DslResult]:
    results: list[DslResult] = []
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        results.append(execute_dsl_line(line, default_file=default_file))
    return results


def dispatch_json(data: bytes) -> DslResult:
    payload = envelope_from_json(data)
    return dispatch(payload)


__all__ = [
    "COMMAND_VERBS",
    "QUERY_VERBS",
    "dispatch",
    "dispatch_json",
    "execute_dsl",
    "execute_dsl_line",
]
