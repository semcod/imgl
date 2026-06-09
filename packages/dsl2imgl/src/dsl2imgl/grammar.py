"""Text DSL → dict for imgl control verbs."""

from __future__ import annotations

import shlex
from typing import Any, Callable


def split_command(line: str) -> list[str]:
    line = line.strip()
    if not line or line.startswith("#"):
        return []
    try:
        return shlex.split(line, posix=True)
    except ValueError:
        return line.split()


def pick_flag(tokens: list[str], flag: str) -> str | None:
    if flag in tokens:
        idx = tokens.index(flag)
        if idx + 1 < len(tokens):
            return tokens[idx + 1]
    return None


def _strip_prompt_tokens(rest: list[str]) -> str:
    cleaned: list[str] = []
    skip_next = False
    for tok in rest:
        if skip_next:
            skip_next = False
            continue
        if tok in {"IMAGE", "WINDOW"}:
            skip_next = True
            continue
        cleaned.append(tok)
    return " ".join(cleaned).strip('"').strip("'")


def _apply_image_window_flags(cmd: dict[str, Any], rest: list[str]) -> None:
    if f := pick_flag(rest, "IMAGE"):
        cmd["image"] = f
    if f := pick_flag(rest, "WINDOW"):
        cmd["window"] = f


def _parse_capture(rest: list[str], cmd: dict[str, Any]) -> None:
    if f := pick_flag(rest, "OUT"):
        cmd["out"] = f
    cmd["interactive"] = "INTERACTIVE" in rest or pick_flag(rest, "INTERACTIVE") == "1"


def _parse_analyze(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["image"] = rest[0] if rest else "screen.png"
    if f := pick_flag(rest, "FILE"):
        cmd["file"] = f
    if f := pick_flag(rest, "WINDOW"):
        cmd["window"] = f
    if "LLM" in rest:
        cmd["llm"] = True


def _parse_actions(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["image"] = rest[0] if rest else "screen.png"
    if f := pick_flag(rest, "WINDOW"):
        cmd["window"] = f
    if "LLM" in rest:
        cmd["llm"] = True


def _parse_resolve(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["prompt"] = _strip_prompt_tokens(rest)
    _apply_image_window_flags(cmd, rest)


def _parse_click(rest: list[str], cmd: dict[str, Any]) -> None:
    if rest and rest[0].isdigit():
        cmd["index"] = int(rest[0])
    else:
        cmd["prompt"] = " ".join(rest).strip('"').strip("'")


def _parse_type(rest: list[str], cmd: dict[str, Any]) -> None:
    if pick_flag(rest, "IN"):
        in_idx = rest.index("IN")
        cmd["value"] = rest[0].strip('"') if rest else ""
        cmd["field"] = " ".join(rest[in_idx + 1 :]).strip('"').split(" IMAGE")[0].split(" WINDOW")[0]
    else:
        cmd["value"] = pick_flag(rest, "VALUE") or (rest[0].strip('"') if rest else "")
        cmd["field"] = pick_flag(rest, "FIELD") or ""


def _parse_key(rest: list[str], cmd: dict[str, Any]) -> None:
    keys_tokens: list[str] = []
    for tok in rest:
        if tok in {"EXECUTE", "IMAGE", "WINDOW"}:
            break
        keys_tokens.append(tok)
    cmd["keys"] = " ".join(keys_tokens) if keys_tokens else "Return"
    if pick_flag(rest, "EXECUTE") == "0":
        cmd["execute"] = False


def _parse_execute(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["prompt"] = " ".join(rest).strip('"').strip("'")


def _parse_interaction_verb(rest: list[str], cmd: dict[str, Any]) -> None:
    verb = str(cmd["verb"]).upper()
    if verb == "CLICK":
        _parse_click(rest, cmd)
    elif verb == "TYPE":
        _parse_type(rest, cmd)
    elif verb == "KEY":
        _parse_key(rest, cmd)
    else:
        _parse_execute(rest, cmd)
    _apply_image_window_flags(cmd, rest)
    if "LLM" in rest:
        cmd["llm"] = True
    cmd["execute"] = pick_flag(rest, "EXECUTE") != "0"


def _parse_agent(rest: list[str], cmd: dict[str, Any]) -> None:
    cmd["goal"] = pick_flag(rest, "GOAL") or " ".join(rest).strip('"').strip("'")
    if f := pick_flag(rest, "MAX"):
        cmd["max_steps"] = int(f)
    _apply_image_window_flags(cmd, rest)


_VERB_PARSERS: dict[str, Callable[[list[str], dict[str, Any]], None]] = {
    "CAPTURE": _parse_capture,
    "ANALYZE": _parse_analyze,
    "ACTIONS": _parse_actions,
    "RESOLVE": _parse_resolve,
    "CLICK": _parse_interaction_verb,
    "TYPE": _parse_interaction_verb,
    "KEY": _parse_interaction_verb,
    "EXECUTE": _parse_interaction_verb,
    "AGENT": _parse_agent,
}


def parse_line(line: str) -> dict[str, Any] | None:
    tokens = split_command(line)
    if not tokens:
        return None
    verb = tokens[0].upper()
    rest = tokens[1:]
    cmd: dict[str, Any] = {"verb": verb}

    if verb == "HEALTH":
        return cmd

    parser = _VERB_PARSERS.get(verb)
    if parser:
        parser(rest, cmd)
        return cmd

    cmd["args"] = rest
    return cmd


def to_text(cmd: dict[str, Any]) -> str:
    verb = str(cmd.get("verb", "")).upper()
    parts = [verb]
    for key in ("image", "prompt", "value", "field", "keys", "goal", "window"):
        if val := cmd.get(key):
            parts.append(f'"{val}"' if " " in str(val) else str(val))
    if idx := cmd.get("index"):
        parts.append(str(idx))
    for key, flag in (
        ("file", "FILE"),
        ("out", "OUT"),
        ("max_steps", "MAX"),
    ):
        if val := cmd.get(key):
            parts.extend([flag, str(val)])
    if cmd.get("llm"):
        parts.append("LLM")
    if cmd.get("interactive"):
        parts.append("INTERACTIVE")
    if cmd.get("execute", True) is not False:
        parts.extend(["EXECUTE", "1"])
    return " ".join(parts)
