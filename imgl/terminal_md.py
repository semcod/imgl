"""ANSI colors for markdown diagnostic reports on stdout."""

from __future__ import annotations

import os
import re
import sys

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"

_FG = {
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "bright_black": "\033[90m",
    "bright_red": "\033[91m",
    "bright_green": "\033[92m",
    "bright_yellow": "\033[93m",
    "bright_blue": "\033[94m",
    "bright_magenta": "\033[95m",
    "bright_cyan": "\033[96m",
    "bright_white": "\033[97m",
}

_VERDICT_COLORS = {
    "stale_capture_error": "bright_red",
    "blank_capture_error": "bright_red",
    "flat_monochrome_error": "bright_red",
    "capture_diagnose_error": "bright_red",
    "operation_failed": "bright_yellow",
    "planned_ok": "bright_green",
    "executed_ok": "bright_green",
    "real_ui": "bright_green",
    "uncertain": "bright_cyan",
}

_FENCE_RE = re.compile(r"^```(\w*)$")
_YAML_KEY_RE = re.compile(r"^(\s*)([A-Za-z0-9_\-]+)(:)(.*)$")
_YAML_LIST_RE = re.compile(r"^(\s*)(-\s+)(.*)$")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_BASH_FLAG_RE = re.compile(r"(--[\w-]+)")
_BASH_STRING_RE = re.compile(r"('[^']*'|\"[^\"]*\")")


def _c(name: str, text: str) -> str:
    return f"{_FG.get(name, '')}{text}{_RESET}"


def stdout_color_enabled() -> bool:
    """Honor NO_COLOR, FORCE_COLOR, IMGL_COLOR and TTY detection."""
    if os.environ.get("NO_COLOR", "").strip():
        return False
    force = os.environ.get("FORCE_COLOR", "").strip().lower()
    if force in {"1", "true", "yes", "on"}:
        return True
    imgl = os.environ.get("IMGL_COLOR", "").strip().lower()
    if imgl in {"0", "false", "no", "off"}:
        return False
    if imgl in {"1", "true", "yes", "on"}:
        return True
    try:
        return bool(sys.stdout.isatty())
    except Exception:
        return False


def _verdict_color(verdict: str) -> str:
    return _VERDICT_COLORS.get(verdict.strip().lower(), "bright_cyan")


def _highlight_yaml_line(line: str) -> str:
    list_match = _YAML_LIST_RE.match(line)
    if list_match:
        indent, dash, rest = list_match.groups()
        return f"{indent}{_c('bright_yellow', dash)}{_color_yaml_value(rest)}"

    key_match = _YAML_KEY_RE.match(line)
    if key_match:
        indent, key, colon, rest = key_match.groups()
        colored_key = _c("bright_cyan", key)
        colored_rest = _color_yaml_value(rest)
        return f"{indent}{colored_key}{colon}{colored_rest}"
    return line


def _color_yaml_value(rest: str) -> str:
    if not rest:
        return ""
    body = rest.lstrip()
    prefix = rest[: len(rest) - len(body)]
    if body.startswith(('"', "'")):
        return prefix + _c("bright_green", body)
    lowered = body.lower()
    if lowered in {"true", "false", "null"}:
        return prefix + _c("bright_magenta", body)
    if re.fullmatch(r"-?\d+(\.\d+)?", body):
        return prefix + _c("bright_yellow", body)
    if body.startswith("`"):
        return prefix + _c("bright_green", body)
    return prefix + _c("white", body)


def _highlight_bash_line(line: str) -> str:
    if not line.strip():
        return line
    parts = line.split()
    out: list[str] = []
    for index, token in enumerate(parts):
        if index > 0:
            out.append(" ")
        if token.startswith("--"):
            out.append(_c("bright_cyan", token))
        elif _BASH_STRING_RE.fullmatch(token):
            out.append(_c("bright_green", token))
        elif index == 0:
            out.append(_c("bright_green", token))
        elif "/" in token or token.endswith(".png") or token.endswith(".json"):
            out.append(_c("bright_blue", token))
        else:
            out.append(_c("white", token))
    return "".join(out)


def _highlight_inline(text: str) -> str:
    def bold_sub(match: re.Match[str]) -> str:
        return f"{_BOLD}{match.group(1)}{_RESET}"

    def code_sub(match: re.Match[str]) -> str:
        value = match.group(1)
        color = _verdict_color(value) if value.endswith("_error") or value.endswith("_ok") else "bright_yellow"
        return _c(color, value)

    text = _BOLD_RE.sub(bold_sub, text)
    return _INLINE_CODE_RE.sub(code_sub, text)


def _render_fence_line(line: str, fence_lang: str) -> str:
    if fence_lang == "yaml":
        return _highlight_yaml_line(line)
    if fence_lang == "bash":
        return _highlight_bash_line(line)
    return _c("white", line)


def _render_normal_line(line: str) -> str:
    if line.startswith("# "):
        return _c("bright_magenta", f"{_BOLD}{line}{_RESET}")
    if line.startswith("## "):
        title = line[3:]
        color = {
            "Current": "bright_yellow",
            "Next": "bright_green",
            "Szczegóły": "bright_cyan",
        }.get(title, "bright_cyan")
        return f"{_FG[color]}{_BOLD}## {title}{_RESET}"
    if line.startswith("**Werdykt:**"):
        match = _INLINE_CODE_RE.search(line)
        if match:
            verdict = match.group(1)
            colored = _c(_verdict_color(verdict), verdict)
            prefix = _highlight_inline(line[: match.start()])
            suffix = line[match.end() :]
            return f"{prefix}`{colored}`{suffix}"
        return _highlight_inline(line)
    if line.startswith("- "):
        return _c("bright_yellow", "- ") + _highlight_inline(line[2:])
    return _highlight_inline(line)


def colorize_markdown(text: str, *, enabled: bool | None = None) -> str:
    """Add ANSI styling for headers, verdict, and fenced yaml/bash blocks."""
    if enabled is None:
        enabled = stdout_color_enabled()
    if not enabled or not text:
        return text

    lines = text.splitlines()
    out: list[str] = []
    in_fence = False
    fence_lang = ""

    for line in lines:
        fence = _FENCE_RE.match(line.strip())
        if fence:
            in_fence = not in_fence
            fence_lang = fence.group(1).lower() if in_fence else ""
            label = fence.group(1) or "code"
            out.append(_c("bright_black", f"```{label}" if in_fence else "```"))
            continue
        if in_fence:
            out.append(_render_fence_line(line, fence_lang))
        else:
            out.append(_render_normal_line(line))

    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def print_report(text: str, fmt: str = "markdown", *, color: bool | None = None) -> None:
    """Print report; colorize markdown code blocks on TTY stdout."""
    if fmt == "markdown":
        text = colorize_markdown(text, enabled=color)
    print(text, end="" if text.endswith("\n") else "\n")


__all__ = ["colorize_markdown", "print_report", "stdout_color_enabled"]
