"""Execute desktop mouse/keyboard actions (optional, Linux-first)."""

from __future__ import annotations

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
    """Run a click/type action on the desktop."""
    kind = action.get("action")
    if kind not in {"click", "type"}:
        return ExecuteResult(ok=False, method="none", message=f"Unsupported action: {kind}")

    x = int(action.get("x", 0))
    y = int(action.get("y", 0))
    if dry_run:
        return ExecuteResult(
            ok=True,
            method="dry-run",
            message=f"{kind} @ ({x}, {y})",
            dry_run=True,
        )

    if shutil.which("xdotool"):
        return _execute_xdotool(kind, x, y, action.get("text", ""))

    if shutil.which("ydotool"):
        return _execute_ydotool(kind, x, y, action.get("text", ""))

    return ExecuteResult(
        ok=False,
        method="none",
        message="No desktop automation tool found (install xdotool or ydotool)",
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
