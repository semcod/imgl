"""NL → imgl DSL line."""

from __future__ import annotations

import re

from dsl2imgl import dispatch
from dsl2imgl.result import DslResult


_KEY_RE = re.compile(
    r"\b(ctrl\+enter|control\+enter|naciśnij enter|naciśnij ctrl\+enter|"
    r"press enter|submit|wyślij|wyslij|zaakceptuj)\b",
    re.IGNORECASE,
)
_TYPE_RE = re.compile(
    r"^(?:wpisz|wprowadź|wprowadz|type)\s+(.+?)(?:\s+(?:w|in|do|into)\s+(.+))?$",
    re.IGNORECASE,
)
_CLICK_RE = re.compile(
    r"\b(kliknij|click|naciśnij|nacisnij|press|tap)\s+(.+)",
    re.IGNORECASE,
)
_CAPTURE_RE = re.compile(r"\b(zrzut|capture|screenshot|ekran)\b", re.IGNORECASE)
_ACTIONS_RE = re.compile(r"\b(akcje|actions|lista|catalog|katalog)\b", re.IGNORECASE)


def to_dsl(
    prompt: str,
    *,
    image: str = "screen.png",
    window: str | None = None,
    execute: bool = True,
) -> str:
    text = prompt.strip()
    flags = f' IMAGE {image}' + (f" WINDOW {window}" if window else "") + (
        " EXECUTE 0" if not execute else " EXECUTE 1"
    )

    if _CAPTURE_RE.search(text):
        return "CAPTURE INTERACTIVE" if "interak" in text.lower() else "CAPTURE"
    if _ACTIONS_RE.search(text):
        llm = " LLM" if "llm" in text.lower() else ""
        return f"ACTIONS {image}{llm}{flags.replace(' IMAGE ' + image, '')}"
    if _KEY_RE.search(text):
        keys = "ctrl+Return" if "ctrl" in text.lower() else "Return"
        return f"KEY {keys}{flags}"
    m = _TYPE_RE.match(text)
    if m:
        value, field = m.group(1).strip('"'), (m.group(2) or "Chat input").strip()
        return f'TYPE "{value}" IN "{field}"{flags}'
    m = _CLICK_RE.search(text)
    if m:
        target = m.group(2).strip()
        if target.isdigit():
            return f"CLICK {target}{flags}"
        return f'EXECUTE "kliknij {target}"{flags}'
    if text.isdigit():
        return f"CLICK {text}{flags}"
    return f'RESOLVE "{text}"{flags}'


def apply_nl(
    prompt: str,
    *,
    image: str = "screen.png",
    window: str | None = None,
    execute: bool = True,
) -> DslResult:
    line = to_dsl(prompt, image=image, window=window, execute=execute)
    if line.startswith("RESOLVE"):
        resolved = dispatch(line)
        if not resolved.ok:
            return resolved
        uri = resolved.data.get("resolved", {}).get("uri")
        if not uri:
            return resolved
        return dispatch(f'EXECUTE "{prompt}" IMAGE {image}' + (f" WINDOW {window}" if window else ""))
    return dispatch(line)
