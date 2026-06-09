"""Runtime handlers — delegate to imgl core (no imgl[web] required)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dsl2imgl.result import DslResult


def _build_interact_session(
    *,
    image: str = "screen.png",
    window: str | None = None,
    use_llm: bool = False,
    lang: str = "eng+pol",
):
    from imgl.interact import InteractSession, _build_session_catalog
    from imgl.scene_cache import load_or_analyze
    from imgl.window_scope import apply_discovered_windows, discover_windows, summarize_windows

    image_path = str(Path(image).expanduser())
    vql_file = str(Path(image_path).with_suffix(".vql.json"))
    scene = load_or_analyze(image_path, vql_file=vql_file, lang=lang, refresh=False)
    windows = discover_windows(scene)
    apply_discovered_windows(scene, windows)
    session = InteractSession(
        image_path=image_path,
        vql_file=vql_file,
        lang=lang,
        scene=scene,
        catalog=[],
        use_llm=use_llm,
        window_summaries=summarize_windows(scene, windows),
        selected_window_id=window,
    )
    if window:
        session.selected_window_id = window
    elif len(session.window_summaries or []) > 1:
        session.selected_window_id = session.window_summaries[0].window.id
    session.catalog = _build_session_catalog(session)
    return session


def _run_prompt_act(
    session,
    *,
    prompt: str | None = None,
    index: int | None = None,
    execute: bool = True,
) -> dict[str, Any]:
    from imgl.execute import execute_action
    from imgl.interact import resolve_imgl_uri
    from imgl.nlp2uri import prompt_to_imgl_uri

    if index is not None:
        prompt = str(index)
    if not prompt:
        return {"ok": False, "message": "prompt/index required"}

    resolved = prompt_to_imgl_uri(
        prompt,
        image=session.image_path,
        file=session.vql_file,
        lang=session.lang,
        catalog=session.catalog,
    )
    if resolved is None:
        return {"ok": False, "message": "Nie rozumiem polecenia"}
    result = resolve_imgl_uri(resolved.uri, session)
    if not result.get("ok"):
        return {"ok": False, "message": str(result.get("error", "unknown")), "resolved": resolved.to_dict()}

    action_payload = {k: v for k, v in result.items() if k not in {"ok", "uri_action"}}
    if action_payload.get("action") not in {"click", "type"}:
        return {
            "ok": True,
            "message": str(action_payload.get("action", "noop")),
            "resolved": resolved.to_dict(),
            "action": action_payload,
        }

    exec_result = execute_action(action_payload, dry_run=not execute)
    return {
        "ok": exec_result.ok,
        "message": exec_result.message,
        "resolved": resolved.to_dict(),
        "action": action_payload,
        "execute": exec_result.to_dict(),
    }


def handle_health(_cmd: dict[str, Any]) -> DslResult:
    return DslResult(ok=True, verb="HEALTH", output="ok", data={"service": "dsl2imgl"})


def handle_capture(cmd: dict[str, Any]) -> DslResult:
    from imgl.capture import capture_screen

    out = cmd.get("out") or "screen.png"
    interactive = bool(cmd.get("interactive"))
    try:
        path = capture_screen(out, interactive=interactive)
        return DslResult(ok=True, verb="CAPTURE", output=str(path), data={"path": str(path)})
    except Exception as exc:
        return DslResult(ok=False, verb="CAPTURE", error=str(exc))


def handle_analyze(cmd: dict[str, Any]) -> DslResult:
    image = cmd.get("image") or "screen.png"
    try:
        session = _build_interact_session(
            image=image,
            window=cmd.get("window"),
            use_llm=bool(cmd.get("llm")),
        )
        return DslResult(
            ok=True,
            verb="ANALYZE",
            output=f"{session.image_path} analyzed",
            data={
                "image_path": session.image_path,
                "window_count": len(session.window_summaries or []),
                "catalog_count": len(session.catalog),
            },
        )
    except Exception as exc:
        return DslResult(ok=False, verb="ANALYZE", error=str(exc))


def handle_actions(cmd: dict[str, Any]) -> DslResult:
    image = cmd.get("image") or "screen.png"
    try:
        session = _build_interact_session(
            image=image,
            window=cmd.get("window"),
            use_llm=bool(cmd.get("llm")),
        )
        actions_payload = [opt.to_dict() for opt in session.catalog[:40]]
        return DslResult(
            ok=True,
            verb="ACTIONS",
            output=json.dumps(actions_payload[:10], ensure_ascii=False),
            data={"actions": actions_payload, "count": len(actions_payload)},
        )
    except Exception as exc:
        return DslResult(ok=False, verb="ACTIONS", error=str(exc))


def handle_resolve(cmd: dict[str, Any]) -> DslResult:
    prompt = cmd.get("prompt") or ""
    if not prompt:
        return DslResult(ok=False, verb="RESOLVE", error="prompt required")
    try:
        session = _build_interact_session(image=cmd.get("image") or "screen.png", window=cmd.get("window"))
        outcome = _run_prompt_act(session, prompt=prompt, execute=False)
        if not outcome.get("ok"):
            return DslResult(ok=False, verb="RESOLVE", error=outcome.get("message", "unresolved"))
        resolved = outcome.get("resolved") or {}
        return DslResult(
            ok=True,
            verb="RESOLVE",
            output=resolved.get("uri", ""),
            data=outcome,
        )
    except Exception as exc:
        return DslResult(ok=False, verb="RESOLVE", error=str(exc))


def handle_execute(cmd: dict[str, Any]) -> DslResult:
    from imgl.execute import execute_action

    verb = str(cmd.get("verb", "")).upper()
    do_execute = cmd.get("execute", True) is not False

    if verb == "KEY":
        action = {"action": "key", "keys": cmd.get("keys") or "Return"}
        try:
            exec_result = execute_action(action, dry_run=not do_execute)
            return DslResult(
                ok=exec_result.ok,
                verb="KEY",
                output=exec_result.message,
                data={"action": action, "execute": exec_result.to_dict()},
            )
        except Exception as exc:
            return DslResult(ok=False, verb="KEY", error=str(exc))

    try:
        session = _build_interact_session(
            image=cmd.get("image") or "screen.png",
            window=cmd.get("window"),
            use_llm=bool(cmd.get("llm")),
        )
        if verb == "TYPE":
            prompt = f"wpisz {cmd.get('value', '')} w {cmd.get('field', 'Chat input')}"
        elif cmd.get("index"):
            prompt = None
            index = int(cmd["index"])
        else:
            prompt = cmd.get("prompt") or ""
            index = None
        if verb != "TYPE" and not prompt and not cmd.get("index"):
            return DslResult(ok=False, verb=verb, error="prompt/index required")

        outcome = _run_prompt_act(
            session,
            prompt=prompt,
            index=cmd.get("index") if cmd.get("index") else None,
            execute=do_execute,
        )
        return DslResult(
            ok=bool(outcome.get("ok")),
            verb=verb,
            output=str(outcome.get("message", "")),
            data=outcome,
            error="" if outcome.get("ok") else str(outcome.get("message", "")),
        )
    except Exception as exc:
        return DslResult(ok=False, verb=verb, error=str(exc))
