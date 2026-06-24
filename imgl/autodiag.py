"""Autodiagnostics: capture quality (img2nl) + operation report for NL control."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from imgl.freshness import image_freshness, sync_vql_cache_with_image

OutputFormat = Literal["auto", "json", "yaml", "markdown"]

_COORD_RE = re.compile(r"@\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)")
_TYPED_RE = re.compile(r"type\s+'([^']*)'")
_KEY_RE = re.compile(r"key\s+(.+)", re.IGNORECASE)

_BLANK_CLASSES = frozenset({"empty_dark_screen", "unchanged_screen", "flat_monochrome"})


def img2nl_root() -> Path:
    raw = os.environ.get("IMG2NL_ROOT", os.path.expanduser("~/github/wronai/img2nl")).strip()
    return Path(raw).expanduser()


def img2nl_available() -> bool:
    from imgl.diagnose import img2nl_available as _avail

    return bool(_avail())


_REAL_UI_CLASSES = {"ui_with_text", "ui_blocks", "dense_ui_or_code", "general"}


def _classify_verdict(
    diag: dict[str, Any],
    is_fresh: bool,
    scene_class: str,
    is_blank: bool,
    worth: bool,
) -> str:
    if not is_fresh:
        return "stale_capture"
    if not diag.get("ok"):
        return "error"
    if is_blank or scene_class in _BLANK_CLASSES:
        return "blank_capture" if scene_class != "flat_monochrome" else "flat_monochrome"
    if scene_class in _REAL_UI_CLASSES or worth:
        return "real_ui"
    return "uncertain"


def diagnose_capture(image_path: str | Path, *, locale: str = "pl") -> dict[str, Any]:
    """Classify screenshot: blank/monochrome vs real UI (via img2nl)."""
    path = Path(image_path).expanduser()
    sync_vql_cache_with_image(path)
    fresh = image_freshness(path)
    if not fresh.get("exists"):
        return {
            "ok": False,
            "path": str(path),
            "error": fresh.get("error"),
            "verdict": "error",
            "img2nl_root": str(img2nl_root()),
            **fresh,
        }

    from imgl.freshness import is_valid_png

    if not is_valid_png(path):
        size = path.stat().st_size
        return {
            "ok": False,
            "path": str(path),
            "error": f"invalid or empty PNG ({size} bytes)",
            "verdict": "blank_capture",
            "scene_class": "empty_dark_screen",
            "summary": (
                f"Zrzut nie jest poprawnym PNG ({size} B) — "
                "uruchom: imgl capture --interactive -o screen.png --verify"
            ),
            "is_blank": True,
            "img2nl_root": str(img2nl_root()),
            **fresh,
        }

    from imgl.diagnose import content_summary, diagnose_content, worth_analyzing

    diag = diagnose_content(path, locale=locale)
    scene_class = str(diag.get("scene_class") or _scene_class(diag))
    worth = worth_analyzing(diag) if diag.get("ok") else False
    is_blank = bool(diag.get("is_blank")) or not worth
    verdict = _classify_verdict(diag, bool(fresh.get("is_fresh")), scene_class, is_blank, worth)

    summary = content_summary(diag, locale=locale)
    if verdict == "stale_capture":
        summary = (
            f"Zrzut przestarzały ({fresh['age_seconds']}s, max {fresh['max_age_seconds']}s) — "
            f"wygenerowano {fresh['mtime_iso']}. Uruchom ponownie `imgl capture --interactive -o <png>`."
        )

    return {
        "ok": bool(diag.get("ok")) and bool(fresh.get("is_fresh")),
        "path": str(path),
        "width": diag.get("width"),
        "height": diag.get("height"),
        "source": diag.get("source", "unknown"),
        "scene_class": scene_class,
        "worth_analyzing": worth,
        "is_blank": is_blank,
        "verdict": verdict,
        "summary": summary,
        "recommendation": diag.get("recommendation", ""),
        "text": diag.get("text", ""),
        "img2nl_available": img2nl_available(),
        "img2nl_root": str(img2nl_root()),
        "features": _compact_features(diag.get("features") or {}),
        "error": diag.get("error"),
        **fresh,
    }


def _extract_result_context(
    result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str]:
    data = result.get("data") or {}
    execute = data.get("execute") or {}
    action = data.get("action") or execute.get("action") or {}
    message = str(
        execute.get("message") or result.get("output") or result.get("error") or ""
    ).strip()
    return data, execute, action, message


def build_operation_step(result: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    data, execute, action, message = _extract_result_context(result)
    verb = str(result.get("verb") or action.get("action") or "").upper() or None
    executed = bool(execute.get("ok")) and not bool(execute.get("dry_run", dry_run))
    method = str(execute.get("method") or ("dry-run" if dry_run else "none"))

    return {
        "verb": verb,
        "command": data.get("command") or result.get("command"),
        "planned": message or result.get("output"),
        "executed": executed,
        "dry_run": bool(execute.get("dry_run", dry_run)),
        "method": method,
        "coordinates": _parse_coords(message) or _coords_from_action(action),
        "text_typed": action.get("text") or _parse_typed_text(message),
        "keys": action.get("keys") or _parse_keys(message),
        "message": message,
        "ok": bool(result.get("ok")),
        "error": result.get("error"),
    }


def _compact_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = {k: v for k, v in result.items() if k != "diagnostics"}
    data = compact.get("data")
    if isinstance(data, dict):
        compact["data"] = {k: v for k, v in data.items() if k != "diagnostics"}
    return compact


def build_execute_report(
    *,
    prompt: str,
    image: str,
    window: str | None,
    dry_run: bool,
    capture: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    operation = build_operation_step(result, dry_run=dry_run)
    capture_ok = (
        capture.get("verdict") in {"real_ui", "uncertain"}
        and capture.get("is_fresh", True)
    )
    op_ok = bool(result.get("ok"))
    executed_for_real = operation.get("executed") and not operation.get("dry_run")

    report: dict[str, Any] = {
        "ok": op_ok and (dry_run or capture_ok),
        "prompt": prompt,
        "image": image,
        "window": window,
        "dry_run": dry_run,
        "capture": capture,
        "operation": operation,
        "result": _compact_result(result),
        "checks": {
            "capture_usable": capture_ok,
            "capture_fresh": bool(capture.get("is_fresh", True)),
            "operation_planned": bool(operation.get("planned")),
            "operation_executed": executed_for_real,
            "blocked_blank_capture": capture.get("verdict") in {"blank_capture", "flat_monochrome"},
            "blocked_stale_capture": capture.get("verdict") == "stale_capture",
        },
        "verdict": _overall_verdict(capture, operation, dry_run=dry_run),
    }
    current, next_cmd = _derive_current_next(report)
    if current:
        report["current"] = current
    if next_cmd:
        report["next_cmd"] = next_cmd
    hints = _actionable_hints(report)
    if hints:
        report["co_zrobic"] = hints
    return report


def resolve_cli_output_format(
    *,
    json_flag: bool = False,
    yaml_flag: bool = False,
    legacy: str | None = None,
) -> OutputFormat:
    """CLI default is markdown; --json / --yaml select structured output."""
    if json_flag and yaml_flag:
        raise ValueError("use only one of --json or --yaml")
    if json_flag:
        return "json"
    if yaml_flag:
        return "yaml"
    if legacy and legacy not in {"auto", "markdown"}:
        return legacy  # type: ignore[return-value]
    return "markdown"


def pick_output_format(payload: dict[str, Any], requested: OutputFormat) -> OutputFormat:
    if requested in {"auto", "markdown"}:
        return "markdown"
    return requested


def render_report(payload: dict[str, Any], fmt: OutputFormat) -> str:
    resolved = pick_output_format(payload, fmt)
    if resolved == "json":
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    if resolved == "yaml":
        import yaml

        return yaml.safe_dump(payload, sort_keys=False, allow_unicode=True)
    return _render_markdown(payload)


def _flag_enabled(*keys: str, default: bool = True) -> bool:
    for key in keys:
        raw = os.environ.get(key, "").strip().lower()
        if raw:
            return raw not in {"0", "false", "no", "off"}
    return default


def should_block_blank_capture(capture: dict[str, Any]) -> bool:
    if not _flag_enabled("IMGL_DIAG_BLOCK", "KORU_IMGL_DIAG_BLOCK"):
        return False
    return capture.get("verdict") in {"blank_capture", "flat_monochrome", "error"}


def should_block_stale_capture(capture: dict[str, Any]) -> bool:
    if not _flag_enabled("IMGL_STALE_BLOCK", "KORU_IMGL_STALE_BLOCK"):
        return False
    return capture.get("verdict") == "stale_capture" or not capture.get("is_fresh", True)


def diagnostics_enabled() -> bool:
    return _flag_enabled("IMGL_DIAG", "KORU_IMGL_DIAG")


def _yaml_codeblock(data: Any) -> str:
    import yaml

    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip()
    return f"```yaml\n{body}\n```"


def _shell_quote(value: str) -> str:
    if not value:
        return "''"
    if re.fullmatch(r"[\w./:@%+\-]+", value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _capture_next_cmd(image: str) -> str:
    return f"imgl capture --interactive -o {_shell_quote(image)} --verify"


def _derive_stale(capture: dict[str, Any], image: str) -> tuple[str, str]:
    age = capture.get("age_seconds")
    max_age = capture.get("max_age_seconds", 60)
    age_bit = f" ({age}s > {max_age}s)" if age is not None else ""
    return (
        f"Zrzut ekranu jest przestarzały{age_bit}. Zrób świeży capture przed planowaniem akcji.",
        _capture_next_cmd(image),
    )


def _derive_op_failed(
    operation: dict[str, Any],
    *,
    prompt: str,
    window: str | None,
    image: str,
) -> tuple[str, str]:
    op_error = str(operation.get("error") or operation.get("message") or "")
    if "element not found" in op_error.lower() or "nie znaleziono" in op_error.lower():
        llm_flag = " --llm" if "llm" not in prompt.lower() else ""
        win_flag = f" --window {_shell_quote(str(window))}" if window else ""
        return (
            "Element UI nie znaleziony na zrzucie. Upewnij się, że pole jest widoczne; "
            "spróbuj ponownie z --llm lub świeżym capture.",
            (
                f"imgl execute {_shell_quote(prompt)}{win_flag} --image "
                f"{_shell_quote(image)}{llm_flag} --dry-run"
                if prompt
                else f"imgl analyze {_shell_quote(image)}"
            ),
        )
    return (
        f"Akcja nie powiodła się: {op_error or 'nieznany błąd'}.",
        f"imgl doctor --image {_shell_quote(image)} --yaml",
    )


def _capture_verdict_current_next(
    capture_verdict: str, image: str, capture: dict[str, Any]
) -> tuple[str, str] | None:
    if capture_verdict == "blank_capture":
        return ("Zrzut pusty lub bez treści UI. Zrób interaktywny capture (portal GNOME).", _capture_next_cmd(image))
    if capture_verdict == "flat_monochrome":
        return ("Zrzut jednokolorowy — brak widocznego UI. Powtórz capture z widocznym pulpitem.", _capture_next_cmd(image))
    if capture_verdict == "error" or not capture.get("exists", True):
        return (f"Brak poprawnego zrzutu ({capture.get('error') or 'plik nie istnieje'}).", _capture_next_cmd(image))
    return None


def _derive_current_next(report: dict[str, Any]) -> tuple[str | None, str | None]:
    """Human status (current) and the single best shell command to run next."""
    capture = report.get("capture") or {}
    operation = report.get("operation") or {}
    image = str(report.get("image") or capture.get("path") or "screen.png")
    prompt = str(report.get("prompt") or "").strip()
    window = report.get("window")
    overall = str(report.get("verdict") or "")
    capture_verdict = str(capture.get("verdict") or "")
    dry_run = bool(report.get("dry_run") or operation.get("dry_run"))

    if overall == "stale_capture_error" or capture_verdict == "stale_capture" or not capture.get("is_fresh", True):
        return _derive_stale(capture, image)

    cv_result = _capture_verdict_current_next(capture_verdict, image, capture)
    if cv_result is not None:
        return cv_result

    if overall == "operation_failed":
        return _derive_op_failed(operation, prompt=prompt, window=window, image=image)

    if dry_run and overall == "planned_ok" and operation.get("ok"):
        win_flag = f" --window {_shell_quote(str(window))}" if window else ""
        return (
            "Plan gotowy (dry-run). Uruchom bez --dry-run, aby wykonać na pulpicie.",
            f"nlp2imgl apply {_shell_quote(prompt)}{win_flag} --image {_shell_quote(image)}",
        )

    if overall == "executed_ok":
        return ("Akcja wykonana na pulpicie. Zweryfikuj efekt w oknie docelowym.", None)

    return (None, None)


_CAPTURE_PAYLOAD_KEYS = (
    "verdict", "scene_class", "source", "path", "width", "height",
    "mtime_iso", "age_seconds", "max_age_seconds", "is_fresh",
    "worth_analyzing", "is_blank", "recommendation", "summary",
    "img2nl_available", "error",
)

_DISPLAY_KEYS = (
    "display", "os_windows", "vision_windows", "correlation",
    "target_os_window", "target_vision_window", "recommendations",
)


def _capture_payload_section(capture: dict[str, Any]) -> dict[str, Any] | None:
    if not (capture.get("path") or capture.get("verdict")):
        return None
    return {k: capture[k] for k in _CAPTURE_PAYLOAD_KEYS if k in capture and capture[k] is not None}


def _markdown_payload(report: dict[str, Any]) -> dict[str, Any]:
    """Structure for markdown YAML blocks (no markdown tables)."""
    capture = report.get("capture") or {}
    payload: dict[str, Any] = {}
    verdict = report.get("verdict") or capture.get("verdict")
    if verdict:
        payload["werdykt"] = verdict
    for key in ("current", "next_cmd", "prompt", "image", "window", "dry_run", "llm_ready"):
        if key in report and report[key] is not None:
            payload[key] = report[key]
    zrzut = _capture_payload_section(capture)
    if zrzut is not None:
        payload["zrzut"] = zrzut
    if report.get("operation"):
        payload["operacja"] = report["operation"]
    if report.get("checks"):
        payload["sprawdzenia"] = report["checks"]
    if report.get("result"):
        payload["wynik"] = report["result"]
    for key in _DISPLAY_KEYS:
        if report.get(key):
            payload[key] = report[key]
    if report.get("co_zrobic"):
        payload["co_zrobic"] = report["co_zrobic"]
    return payload


def _render_markdown(report: dict[str, Any]) -> str:
    verdict = report.get("verdict") or report.get("capture", {}).get("verdict", "?")
    current = report.get("current")
    next_cmd = report.get("next_cmd")
    if not current and not next_cmd:
        current, next_cmd = _derive_current_next(report)

    lines = ["# imgl — autodiagnostyka", "", f"**Werdykt:** `{verdict}`", ""]
    if current:
        lines.extend(["## Current", "", current, ""])
    if next_cmd:
        lines.extend(["## Next", "", f"```bash", next_cmd, "```", ""])
    lines.extend(["## Szczegóły", "", _yaml_codeblock(_markdown_payload(report))])
    return "\n".join(lines).rstrip() + "\n"


def _overall_verdict(capture: dict[str, Any], operation: dict[str, Any], *, dry_run: bool) -> str:
    if capture.get("verdict") == "stale_capture" or not capture.get("is_fresh", True):
        return "stale_capture_error"
    if capture.get("verdict") == "blank_capture":
        return "blank_capture_error"
    if capture.get("verdict") == "flat_monochrome":
        return "flat_monochrome_error"
    if capture.get("verdict") == "error":
        return "capture_diagnose_error"
    if not operation.get("ok"):
        return "operation_failed"
    if dry_run or operation.get("dry_run"):
        return "planned_ok"
    if operation.get("executed"):
        return "executed_ok"
    return "uncertain"


def _capture_verdict_hints(capture: dict[str, Any], image: str) -> list[str]:
    verdict = capture.get("verdict")
    if verdict == "stale_capture" or not capture.get("is_fresh", True):
        return [
            f"Zrzut starszy niż {capture.get('max_age_seconds', 60)}s — "
            f"`{_capture_next_cmd(image)}`, potem ponów execute/apply."
        ]
    if verdict == "blank_capture":
        return [f"Zrzut pusty — `{_capture_next_cmd(image)}`."]
    if verdict == "flat_monochrome":
        return [f"Zrzut jednokolorowy — `{_capture_next_cmd(image)}`."]
    if verdict == "error":
        return [f"img2nl: `pip install -e {img2nl_root()}[analyze]`."]
    return []


def _actionable_hints(report: dict[str, Any]) -> list[str]:
    capture = report.get("capture") or {}
    operation = report.get("operation") or {}
    image = str(report.get("image") or capture.get("path") or "screen.png")

    hints = _capture_verdict_hints(capture, image)

    op_error = str(operation.get("error") or operation.get("message") or "")
    if "element not found" in op_error.lower():
        hints.append(
            "Element nie na zrzucie — upewnij się, że chat/input jest widoczny; "
            "użyj `--llm` lub świeżego capture."
        )

    if report.get("dry_run") or operation.get("dry_run"):
        if report.get("verdict") == "planned_ok":
            hints.append("Dry-run OK — uruchom `nlp2imgl apply` bez `--dry-run`.")
        elif report.get("verdict") != "stale_capture_error":
            hints.append("Dry-run — użyj `nlp2imgl apply` bez `--dry-run` lub REST execute=true.")
    elif operation.get("executed") and operation.get("text_typed"):
        hints.append(
            f"Wpisano `{operation['text_typed']}` @ {operation.get('coordinates')} — "
            "upewnij się, że okno docelowe było na wierzchu."
        )
    return hints


def _compact_features(features: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for block, keys in (
        ("scene", ("scene_class", "labels")),
        ("colors", ("unique_colors_sampled", "is_monochrome", "is_mostly_dark")),
        ("edges", ("edge_density", "text_likelihood")),
        ("objects", ("has_large_objects", "many_objects")),
    ):
        src = features.get(block) or {}
        if src:
            out[block] = {k: src[k] for k in keys if k in src}
    return out


def _scene_class(diag: dict[str, Any]) -> str:
    return str((diag.get("features") or {}).get("scene", {}).get("scene_class", "general"))


def _parse_coords(message: str) -> list[int] | None:
    match = _COORD_RE.search(message)
    return [int(match.group(1)), int(match.group(2))] if match else None


def _coords_from_action(action: dict[str, Any]) -> list[int] | None:
    if "x" in action and "y" in action:
        return [int(action["x"]), int(action["y"])]
    return None


def _parse_typed_text(message: str) -> str | None:
    match = _TYPED_RE.search(message)
    return match.group(1) if match else None


def _parse_keys(message: str) -> str | None:
    match = _KEY_RE.search(message)
    return match.group(1).strip() if match else None


__all__ = [
    "OutputFormat",
    "build_execute_report",
    "build_operation_step",
    "diagnose_capture",
    "diagnostics_enabled",
    "img2nl_available",
    "img2nl_root",
    "pick_output_format",
    "resolve_cli_output_format",
    "render_report",
    "should_block_blank_capture",
    "should_block_stale_capture",
]
