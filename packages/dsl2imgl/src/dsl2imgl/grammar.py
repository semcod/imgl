"""Text DSL → dict for imgl control verbs."""

from __future__ import annotations

import shlex
from typing import Any


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


def parse_line(line: str) -> dict[str, Any] | None:
    tokens = split_command(line)
    if not tokens:
        return None
    verb = tokens[0].upper()
    rest = tokens[1:]
    cmd: dict[str, Any] = {"verb": verb}

    if verb == "HEALTH":
        return cmd
    if verb == "CAPTURE":
        if f := pick_flag(rest, "OUT"):
            cmd["out"] = f
        cmd["interactive"] = "INTERACTIVE" in rest or pick_flag(rest, "INTERACTIVE") == "1"
    elif verb == "ANALYZE":
        cmd["image"] = rest[0] if rest else "screen.png"
        if f := pick_flag(rest, "FILE"):
            cmd["file"] = f
        if f := pick_flag(rest, "WINDOW"):
            cmd["window"] = f
        if "LLM" in rest:
            cmd["llm"] = True
    elif verb == "ACTIONS":
        cmd["image"] = rest[0] if rest else "screen.png"
        if f := pick_flag(rest, "WINDOW"):
            cmd["window"] = f
        if "LLM" in rest:
            cmd["llm"] = True
    elif verb == "RESOLVE":
        cleaned: list[str] = []
        skip_next = False
        for i, tok in enumerate(rest):
            if skip_next:
                skip_next = False
                continue
            if tok in {"IMAGE", "WINDOW"}:
                skip_next = True
                continue
            cleaned.append(tok)
        cmd["prompt"] = " ".join(cleaned).strip('"').strip("'")
        if f := pick_flag(rest, "IMAGE"):
            cmd["image"] = f
        if f := pick_flag(rest, "WINDOW"):
            cmd["window"] = f
    elif verb in {"CLICK", "TYPE", "KEY", "EXECUTE"}:
        if verb == "CLICK":
            if rest and rest[0].isdigit():
                cmd["index"] = int(rest[0])
            else:
                cmd["prompt"] = " ".join(rest).strip('"').strip("'")
        elif verb == "TYPE":
            if pick_flag(rest, "IN"):
                in_idx = rest.index("IN")
                cmd["value"] = rest[0].strip('"') if rest else ""
                cmd["field"] = " ".join(rest[in_idx + 1 :]).strip('"').split(" IMAGE")[0].split(" WINDOW")[0]
            else:
                cmd["value"] = pick_flag(rest, "VALUE") or (rest[0].strip('"') if rest else "")
                cmd["field"] = pick_flag(rest, "FIELD") or ""
        elif verb == "KEY":
            keys_tokens: list[str] = []
            for tok in rest:
                if tok in {"EXECUTE", "IMAGE", "WINDOW"}:
                    break
                keys_tokens.append(tok)
            cmd["keys"] = " ".join(keys_tokens) if keys_tokens else "Return"
            if pick_flag(rest, "EXECUTE") == "0":
                cmd["execute"] = False
        else:
            cmd["prompt"] = " ".join(rest).strip('"').strip("'")
        if f := pick_flag(rest, "IMAGE"):
            cmd["image"] = f
        if f := pick_flag(rest, "WINDOW"):
            cmd["window"] = f
        if "LLM" in rest:
            cmd["llm"] = True
        cmd["execute"] = pick_flag(rest, "EXECUTE") != "0"
    elif verb == "AGENT":
        cmd["goal"] = pick_flag(rest, "GOAL") or " ".join(rest).strip('"').strip("'")
        if f := pick_flag(rest, "MAX"):
            cmd["max_steps"] = int(f)
        if f := pick_flag(rest, "IMAGE"):
            cmd["image"] = f
        if f := pick_flag(rest, "WINDOW"):
            cmd["window"] = f
    else:
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
