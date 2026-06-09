"""NL → imgl DSL line."""

from __future__ import annotations

import os
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


def use_llm_enabled(explicit: bool | None = None) -> bool:
    if explicit is not None:
        return explicit
    raw = os.environ.get("IMGL_USE_LLM", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    try:
        from imgl.llm_catalog import _load_env_files

        _load_env_files()
    except ImportError:
        pass
    return bool(os.environ.get("OPENROUTER_API_KEY", "").strip())


def to_dsl(
    prompt: str,
    *,
    image: str = "screen.png",
    window: str | None = None,
    execute: bool = True,
    use_llm: bool | None = None,
) -> str:
    text = prompt.strip()
    llm_flag = " LLM" if use_llm_enabled(use_llm) or "llm" in text.lower() else ""
    flags = f' IMAGE {image}' + (f" WINDOW {window}" if window else "") + llm_flag + (
        " EXECUTE 0" if not execute else " EXECUTE 1"
    )

    if _CAPTURE_RE.search(text):
        return "CAPTURE INTERACTIVE" if "interak" in text.lower() else "CAPTURE"
    if _ACTIONS_RE.search(text):
        return f"ACTIONS {image}{llm_flag}{flags.replace(' IMAGE ' + image, '')}"
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
    use_llm: bool | None = None,
) -> DslResult:
    line = to_dsl(prompt, image=image, window=window, execute=execute, use_llm=use_llm)
    if line.startswith("RESOLVE"):
        resolved = dispatch(line)
        if not resolved.ok:
            return resolved
        uri = resolved.data.get("resolved", {}).get("uri")
        if not uri:
            return resolved
        return dispatch(f'EXECUTE "{prompt}" IMAGE {image}' + (f" WINDOW {window}" if window else ""))
    return dispatch(line)
