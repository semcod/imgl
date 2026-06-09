"""Execute desktop mouse/keyboard actions (optional, Linux-first)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class ExecuteResult:
    ok: bool
    method: str
    message: str
    dry_run: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "method": self.method,
            "message": self.message,
            "dry_run": self.dry_run,
        }


def execute_action(action: dict[str, Any], *, dry_run: bool = False) -> ExecuteResult:
    """Run a click/type/key action on the desktop."""
    mismatch = _display_mismatch_warning(action)
    strict = os.environ.get("IMGL_STRICT_DISPLAY", "").strip().lower() in {"1", "true", "yes", "on"}
    if mismatch and strict and not dry_run:
        return ExecuteResult(ok=False, method="display-guard", message=mismatch)

    kind = action.get("action")
    if kind == "key":
        keys = str(action.get("keys") or action.get("text") or "")
        if dry_run:
            return ExecuteResult(ok=True, method="dry-run", message=f"key {keys}", dry_run=True)
        result = execute_keys(keys)
        return _append_display_warning(result, mismatch)

    if kind not in {"click", "type"}:
        return ExecuteResult(ok=False, method="none", message=f"Unsupported action: {kind}")

    x = int(action.get("x", 0))
    y = int(action.get("y", 0))
    if dry_run:
        message = f"{kind} @ ({x}, {y})"
        if mismatch:
            message = f"{message}; warning: {mismatch}"
        return ExecuteResult(
            ok=True,
            method="dry-run",
            message=message,
            dry_run=True,
        )

    if shutil.which("xdotool"):
        result = _execute_xdotool(kind, x, y, action.get("text", ""))
        return _append_display_warning(result, mismatch)

    if shutil.which("ydotool"):
        result = _execute_ydotool(kind, x, y, action.get("text", ""))
        return _append_display_warning(result, mismatch)

    return ExecuteResult(
        ok=False,
        method="none",
        message="No desktop automation tool found (install xdotool or ydotool)",
    )


def _display_mismatch_warning(action: dict[str, Any]) -> str | None:
    image = action.get("image_path") or action.get("source_image")
    if not image:
        return None
    try:
        from imgl.capture_provenance import load_capture_meta

        capture = load_capture_meta(image)
    except ImportError:
        return None
    capture_display = str(capture.get("display") or "").strip()
    if not capture_display:
        return None
    current = os.environ.get("DISPLAY", "").strip()
    if current and capture_display != current:
        return f"DISPLAY mismatch: captured on {capture_display}, executing on {current}"
    return None


def _append_display_warning(result: ExecuteResult, warning: str | None) -> ExecuteResult:
    if not warning or not result.ok:
        return result
    return ExecuteResult(
        ok=result.ok,
        method=result.method,
        message=f"{result.message}; warning: {warning}",
        dry_run=result.dry_run,
    )


def _execute_xdotool(kind: str, x: int, y: int, text: str) -> ExecuteResult:
    try:
        subprocess.run(
            ["xdotool", "mousemove", str(x), str(y)],
            check=True,
            capture_output=True,
            text=True,
        )
        if kind == "click":
            subprocess.run(
                ["xdotool", "click", "1"],
                check=True,
                capture_output=True,
                text=True,
            )
            return ExecuteResult(ok=True, method="xdotool", message=f"click @ ({x}, {y})")
        subprocess.run(["xdotool", "click", "1"], check=True, capture_output=True, text=True)
        time.sleep(0.05)
        if text:
            subprocess.run(
                ["xdotool", "type", "--delay", "12", "--", text],
                check=True,
                capture_output=True,
                text=True,
            )
        return ExecuteResult(ok=True, method="xdotool", message=f"type '{text}' @ ({x}, {y})")
    except subprocess.CalledProcessError as exc:
        return ExecuteResult(ok=False, method="xdotool", message=exc.stderr or str(exc))


def _execute_ydotool(kind: str, x: int, y: int, text: str) -> ExecuteResult:
    try:
        subprocess.run(
            ["ydotool", "mousemove", "--absolute", str(x), str(y)],
            check=True,
            capture_output=True,
            text=True,
        )
        if kind == "click":
            subprocess.run(["ydotool", "click", "0xC0"], check=True, capture_output=True, text=True)
            return ExecuteResult(ok=True, method="ydotool", message=f"click @ ({x}, {y})")
        subprocess.run(["ydotool", "click", "0xC0"], check=True, capture_output=True, text=True)
        if text:
            subprocess.run(["ydotool", "type", text], check=True, capture_output=True, text=True)
        return ExecuteResult(ok=True, method="ydotool", message=f"type '{text}' @ ({x}, {y})")
    except subprocess.CalledProcessError as exc:
        return ExecuteResult(ok=False, method="ydotool", message=exc.stderr or str(exc))


def execute_keys(keys: str) -> ExecuteResult:
    """Send keyboard shortcut via xdotool (e.g. ctrl+Return, Return, Tab)."""
    normalized = _normalize_keys(keys)
    if not normalized:
        return ExecuteResult(ok=False, method="none", message=f"Unsupported keys: {keys}")
    if shutil.which("xdotool"):
        try:
            subprocess.run(
                ["xdotool", "key", "--", normalized],
                check=True,
                capture_output=True,
                text=True,
            )
            return ExecuteResult(ok=True, method="xdotool", message=f"key {normalized}")
        except subprocess.CalledProcessError as exc:
            return ExecuteResult(ok=False, method="xdotool", message=exc.stderr or str(exc))
    return ExecuteResult(
        ok=False,
        method="none",
        message="KEY requires xdotool (ydotool key combos not supported yet)",
    )


def _normalize_keys(keys: str) -> str:
    text = keys.strip().lower().replace(" ", "")
    aliases = {
        "enter": "Return",
        "return": "Return",
        "ctrl+enter": "ctrl+Return",
        "control+enter": "ctrl+Return",
        "ctrl+return": "ctrl+Return",
        "shift+enter": "shift+Return",
        "escape": "Escape",
        "esc": "Escape",
        "tab": "Tab",
    }
    if text in aliases:
        return aliases[text]
    if "+" in text:
        parts = text.split("+")
        mapped = []
        for part in parts:
            if part in {"ctrl", "control"}:
                mapped.append("ctrl")
            elif part in {"shift", "alt", "super", "meta"}:
                mapped.append(part if part != "meta" else "super")
            elif part in {"enter", "return"}:
                mapped.append("Return")
            else:
                mapped.append(part.capitalize() if len(part) > 1 else part)
        return "+".join(mapped)
    return keys.strip()
