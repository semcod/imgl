"""Interactive shell for choosing UI actions from screenshot analysis."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import parse_qs, urlparse

from imgl.actions import ElementNotFoundError, actions
from imgl.catalog import InteractiveOption, build_interactive_catalog, format_catalog_table
from imgl.config import ImglConfig
from imgl.execute import ExecuteResult, execute_action
from imgl.export import (
    default_annotated_path,
    open_image,
    write_annotated_image,
    write_vql_program,
    write_window_preview_images,
)
from imgl.nlp2uri import ResolvedImglUri, prompt_to_imgl_uri
from imgl.scene_cache import load_or_analyze, save_scene_cache
from imgl.uri import uri_for_imgl_annotate, uri_for_imgl_list
from imgl.window_scope import (
    WindowSummary,
    apply_discovered_windows,
    discover_windows,
    export_window_crop,
    format_window_picker,
    get_discovered_window,
    summarize_windows,
)


@dataclass
class InteractSession:
    image_path: str
    vql_file: str
    lang: str
    scene: Any
    catalog: list[InteractiveOption]
    annotated_path: str | None = None
    filter_noise: bool = True
    use_llm: bool = False
    llm_model: str = "openrouter/google/gemini-3.1-flash-image-preview"
    catalog_max_items: int = 40
    selected_window_id: str | None = None
    window_summaries: list[WindowSummary] | None = None
    phase: str = "actions"
    annotate: bool = False
    open_annotated: bool = False
    annotated_output: str | None = None
    viewer_opened: bool = False


def _build_session_catalog(
    session: InteractSession,
    *,
    refresh_scene: bool = False,
) -> list[InteractiveOption]:
    scene = session.scene
    if refresh_scene:
        scene = session.scene
    return build_interactive_catalog(
        scene,
        image_path=session.image_path,
        vql_file=session.vql_file,
        lang=session.lang,
        filter_noise=session.filter_noise,
        use_llm=session.use_llm,
        llm_model=session.llm_model,
        max_items=session.catalog_max_items,
        window_id=session.selected_window_id,
        include_window_entries=session.selected_window_id is None,
    )


def resolve_imgl_uri(
    uri: str,
    session: InteractSession,
) -> dict[str, Any]:
    """Resolve vql://window/imgl?action=... to concrete action payload."""
    parsed = urlparse(uri)
    if parsed.scheme != "vql":
        return {"ok": False, "error": f"Not a vql:// URI: {uri}"}

    selector = (parsed.netloc + parsed.path).strip("/")
    if selector not in {"window/imgl", "imgl"}:
        return {"ok": False, "error": f"Unsupported selector: {selector}"}

    qs = parse_qs(parsed.query)
    action_name = (qs.get("action") or ["analyze"])[0].strip().lower()
    finder = actions(session.scene)

    if action_name in {"quit", "exit"}:
        return {"ok": True, "action": "quit"}

    if action_name == "list":
        return {
            "ok": True,
            "action": "list",
            "options": [opt.to_dict() for opt in session.catalog],
            "count": len(session.catalog),
        }

    if action_name in {"annotate", "map", "numbered"}:
        output_raw = (qs.get("output") or [""])[0] or None
        return _annotate_catalog(session, output_path=output_raw)

    if action_name == "analyze":
        scene = load_or_analyze(
            session.image_path,
            vql_file=session.vql_file,
            lang=session.lang,
            config=ImglConfig(),
            refresh=True,
        )
        write_vql_program(scene, session.vql_file)
        save_scene_cache(scene, session.vql_file)
        session.scene = scene
        session.catalog = _build_session_catalog(session, refresh_scene=True)
        return {
            "ok": True,
            "action": "analyze",
            "element_count": len(session.catalog),
            "program": session.vql_file,
        }

    if action_name == "click":
        return _resolve_click(qs, finder, session)

    if action_name == "type":
        return _resolve_type(qs, finder, session)

    return {"ok": False, "error": f"Unknown action: {action_name}"}


def _attach_image_path(payload: dict[str, Any], session: InteractSession) -> dict[str, Any]:
    enriched = dict(payload)
    enriched["image_path"] = session.image_path
    return enriched


def _click_by_element_id(element_id: str, session: InteractSession) -> dict[str, Any] | None:
    for option in session.catalog:
        if option.element_id != element_id:
            continue
        payload = dict(option.action_payload)
        payload["action"] = "click"
        if option.category == "input":
            payload["hint"] = (
                f"Pole input — fokus. Wpisz tekst: "
                f"wpisz WARTOŚĆ w {option.label!r}"
            )
        return {"ok": True, "uri_action": "click", **_attach_image_path(payload, session)}
    return None


def _resolve_click(qs: dict[str, list[str]], finder, session: InteractSession) -> dict[str, Any]:
    element_id = (qs.get("element_id") or [""])[0] or None
    text = (qs.get("text") or [""])[0] or None
    label = (qs.get("label") or [""])[0] or None
    window = (qs.get("window") or [""])[0] or None
    element_type = (qs.get("element_type") or [""])[0] or None

    if element_id:
        result = _click_by_element_id(element_id, session)
        return result if result is not None else {"ok": False, "error": f"element_id not found: {element_id}"}

    try:
        payload = finder.click(element_type or None, text=text, label=label, window=window)
        return {"ok": True, "uri_action": "click", **_attach_image_path(payload, session)}
    except ElementNotFoundError as exc:
        return {"ok": False, "error": str(exc)}


def _resolve_type_no_value(qs: dict[str, list[str]], session: InteractSession) -> dict[str, Any]:
    element_id = (qs.get("element_id") or [""])[0] or None
    hint = "type action requires value= (np. wpisz hello w Username)"
    if element_id:
        for option in session.catalog:
            if option.element_id == element_id and option.category == "input":
                hint = (
                    f"Brak value=. Wybierz numer {option.index} aby ustawić fokus, "
                    f"lub: wpisz TEKST w {option.label!r}"
                )
                break
    return {"ok": False, "error": hint}


def _resolve_type_by_element_id(
    element_id: str,
    value: str,
    session: InteractSession,
) -> dict[str, Any] | None:
    for option in session.catalog:
        if option.element_id == element_id and option.category == "input":
            payload = dict(option.action_payload)
            payload["action"] = "type"
            payload["text"] = value
            return {"ok": True, "uri_action": "type", **_attach_image_path(payload, session)}
    return None


def _resolve_type_by_hints(
    label: str | None,
    text: str | None,
    value: str,
    session: InteractSession,
) -> dict[str, Any] | None:
    for hint in (label, text):
        if not hint:
            continue
        query = hint.casefold()
        for option in session.catalog:
            if option.category != "input":
                continue
            for candidate in (option.label, option.text):
                if not candidate:
                    continue
                cand = candidate.casefold()
                if query == cand or query in cand or cand in query:
                    payload = dict(option.action_payload)
                    payload["action"] = "type"
                    payload["text"] = value
                    return {"ok": True, "uri_action": "type", **_attach_image_path(payload, session)}
    return None


def _resolve_type(qs: dict[str, list[str]], finder, session: InteractSession) -> dict[str, Any]:
    if not qs.get("value"):
        return _resolve_type_no_value(qs, session)
    value = qs["value"][0]
    text = (qs.get("text") or [""])[0] or None
    label = (qs.get("label") or [""])[0] or None
    window = (qs.get("window") or [""])[0] or None
    element_id = (qs.get("element_id") or [""])[0] or None

    if element_id:
        result = _resolve_type_by_element_id(element_id, value, session)
        if result:
            return result

    result = _resolve_type_by_hints(label, text, value, session)
    if result:
        return result

    try:
        payload = finder.type_into(value, label=label, text=text, window=window)
        return {"ok": True, "uri_action": "type", **_attach_image_path(payload, session)}
    except ElementNotFoundError as exc:
        return {"ok": False, "error": str(exc)}


def _annotate_catalog(
    session: InteractSession,
    *,
    output_path: str | None = None,
    open_viewer: bool = False,
) -> dict[str, Any]:
    window = (
        get_discovered_window(session.scene, session.selected_window_id)
        if session.selected_window_id
        else None
    )
    out = Path(output_path) if output_path else default_annotated_path(
        session.image_path,
        window_id=session.selected_window_id,
    )
    path = write_annotated_image(
        session.scene,
        session.catalog,
        out,
        source_image=session.image_path,
        window=window,
    )
    session.annotated_path = str(path)
    opened = False
    if open_viewer and not session.viewer_opened:
        opened = open_image(path)
        if opened:
            session.viewer_opened = True
    return {
        "ok": True,
        "action": "annotate",
        "path": str(path),
        "count": len(session.catalog),
        "opened": opened,
    }


def _select_window(session: InteractSession, window_ref: str | int) -> bool:
    window = get_discovered_window(session.scene, window_ref)
    if window is None:
        return False
    session.selected_window_id = window.id
    session.phase = "actions"
    session.catalog = _build_session_catalog(session)
    if session.annotate or session.open_annotated:
        out = session.annotated_output or default_annotated_path(
            session.image_path,
            window_id=window.id,
        )
        payload = _annotate_catalog(
            session,
            output_path=str(out),
            open_viewer=session.open_annotated and not session.viewer_opened,
        )
        print(f"Mapa numerów: {payload['path']}", file=sys.stderr)
    return True


def _export_window_previews(session: InteractSession) -> list[str]:
    windows = discover_windows(session.scene)
    paths = write_window_preview_images(
        session.scene,
        windows,
        output_dir=Path(session.image_path).parent,
        source_image=session.image_path,
    )
    for summary, path in zip(session.window_summaries or [], paths, strict=False):
        summary.annotated_path = str(path)
    return [str(path) for path in paths]


def _prepare_interactive_session(
    image_path: str | Path,
    *,
    vql_file: str | Path,
    lang: str,
    config: ImglConfig | None,
    use_llm: bool,
    no_filter: bool,
    annotate: bool,
    open_annotated: bool,
    annotated_output: str | Path | None,
    stderr: TextIO,
) -> tuple[InteractSession, str, str, list[Any]]:
    image = str(Path(image_path).resolve())
    vql_path = str(Path(vql_file).resolve())
    cfg = config or ImglConfig()

    print(f"Analizuję: {image}", file=stderr)
    scene = load_or_analyze(image, vql_file=vql_path, lang=lang, config=cfg)
    scene = apply_discovered_windows(scene)
    write_vql_program(scene, vql_path)
    save_scene_cache(scene, vql_path)
    discovered = discover_windows(scene)
    session = InteractSession(
        image_path=image,
        vql_file=vql_path,
        lang=lang,
        scene=scene,
        catalog=[],
        filter_noise=not no_filter,
        use_llm=use_llm or cfg.use_llm_catalog,
        llm_model=cfg.llm_vision_model,
        catalog_max_items=cfg.catalog_max_items,
        window_summaries=summarize_windows(scene, image_path=image),
        annotate=annotate,
        open_annotated=open_annotated,
        annotated_output=str(annotated_output) if annotated_output else None,
    )
    return session, image, vql_path, discovered


def _show_initial_shell_views(
    *,
    session: InteractSession,
    discovered: list[Any],
    window: str | None,
    cfg: ImglConfig,
    use_llm: bool,
    no_filter: bool,
    stdout: TextIO,
    stderr: TextIO,
) -> int | None:
    print(f"Wykryto okien/regiónów: {len(discovered)}", file=stderr)
    if use_llm or cfg.use_llm_catalog:
        print(
            "Tip: przy --llm najpierw wybierz okno (np. 2=GitHub), potem klikaj elementy.",
            file=stderr,
        )
    if len(discovered) > 1:
        print(format_window_picker(session.window_summaries or [], scene=session.scene), file=stdout)
        if window:
            if not _select_window(session, window):
                print(f"Nie znaleziono okna: {window}", file=stderr)
                return 1
            _print_catalog_banner(session, cfg, use_llm, no_filter, stderr)
            print(format_catalog_table(session.catalog), file=stdout)
        else:
            session.phase = "windows"
            print(
                "Wybierz okno do analizy (numer), 'podglad' (wycinki PNG), "
                "'wszystkie' (cały ekran), 'quit'.",
                file=stderr,
            )
    else:
        session.selected_window_id = discovered[0].id if discovered else None
        session.catalog = _build_session_catalog(session)
        _print_catalog_banner(session, cfg, use_llm, no_filter, stderr)
        print(format_catalog_table(session.catalog), file=stdout)
    return None


def _print_actions_phase_hints(
    *,
    session: InteractSession,
    image: str,
    vql_path: str,
    lang: str,
    annotate: bool,
    open_annotated: bool,
    annotated_output: str | Path | None,
    stderr: TextIO,
) -> None:
    if session.phase != "actions":
        return
    print(f"VQL program: {vql_path}", file=stderr)
    print(f"Lista URI: {uri_for_imgl_list(image=image, file=vql_path, lang=lang)}", file=stderr)
    if (annotate or open_annotated) and not session.annotated_path:
        out = annotated_output or default_annotated_path(
            image,
            window_id=session.selected_window_id,
        )
        payload = _annotate_catalog(
            session,
            output_path=str(out),
            open_viewer=open_annotated,
        )
        print(f"Mapa numerów: {payload['path']}", file=stderr)
        if open_annotated and not payload.get("opened"):
            print("Nie udało się otworzyć podglądu (brak xdg-open).", file=stderr)
    elif session.annotated_path:
        print(f"Mapa numerów: {session.annotated_path}", file=stderr)
    print("", file=stderr)
    print(
        "Tryb interaktywny — numer, NL ('kliknij Save'), 'mapa', 'okna' (zmień okno), 'quit'.",
        file=stderr,
    )


def _read_shell_prompt(stdin: TextIO, stderr: TextIO) -> str | None:
    try:
        if stdin is not sys.stdin:
            line = stdin.readline()
            if not line:
                raise EOFError
            prompt = line.strip()
            print("Co chcesz zrobić?", prompt, file=stderr)
            return prompt
        return input("Co chcesz zrobić? ").strip()
    except (EOFError, KeyboardInterrupt):
        return None


def _handle_resolved_shell_action(
    *,
    result: dict[str, Any],
    session: InteractSession,
    execute: bool,
    stdout: TextIO,
) -> bool:
    """Handle one resolved URI. Returns True to continue the shell loop."""
    if result.get("action") == "annotate":
        print(f"Zapisano mapę numerów: {result.get('path')}", file=stdout)
        if result.get("opened"):
            print("Otwarto podgląd obrazu.", file=stdout)
        return True

    if result.get("action") == "list":
        session.catalog = _build_session_catalog(session)
        print(format_catalog_table(session.catalog), file=stdout)
        return True

    if result.get("action") == "analyze":
        print(
            f"Odświeżono layout — {result.get('element_count', 0)} opcji.",
            file=stdout,
        )
        print(format_catalog_table(session.catalog), file=stdout)
        return True

    if not result.get("ok"):
        print(f"Błąd: {result.get('error', 'unknown')}", file=stdout)
        return True

    action_payload = {k: v for k, v in result.items() if k not in {"ok", "uri_action"}}
    print(json.dumps(action_payload, indent=2, ensure_ascii=False), file=stdout)

    if execute and action_payload.get("action") in {"click", "type"}:
        exec_result = execute_action(action_payload, dry_run=False)
        print(f"Wykonano: {exec_result.message} [{exec_result.method}]", file=stdout)
    elif action_payload.get("action") in {"click", "type"}:
        dry = execute_action(action_payload, dry_run=True)
        print(f"Dry-run: {dry.message} (dodaj --execute aby wykonać)", file=stdout)

    print("", file=stdout)
    return True


def run_interactive_shell(
    image_path: str | Path,
    *,
    vql_file: str | Path = "layout.vql.json",
    lang: str = "eng",
    config: ImglConfig | None = None,
    execute: bool = False,
    use_llm: bool = False,
    no_filter: bool = False,
    annotate: bool = False,
    open_annotated: bool = False,
    annotated_output: str | Path | None = None,
    window: str | None = None,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> int:
    """Analyze screenshot and run an interactive action picker."""
    stdin = input_stream or sys.stdin
    stdout = output_stream or sys.stdout
    stderr = sys.stderr
    cfg = config or ImglConfig()

    session, image, vql_path, discovered = _prepare_interactive_session(
        image_path,
        vql_file=vql_file,
        lang=lang,
        config=cfg,
        use_llm=use_llm,
        no_filter=no_filter,
        annotate=annotate,
        open_annotated=open_annotated,
        annotated_output=annotated_output,
        stderr=stderr,
    )
    early_exit = _show_initial_shell_views(
        session=session,
        discovered=discovered,
        window=window,
        cfg=cfg,
        use_llm=use_llm,
        no_filter=no_filter,
        stdout=stdout,
        stderr=stderr,
    )
    if early_exit is not None:
        return early_exit

    _print_actions_phase_hints(
        session=session,
        image=image,
        vql_path=vql_path,
        lang=lang,
        annotate=annotate,
        open_annotated=open_annotated,
        annotated_output=annotated_output,
        stderr=stderr,
    )

    return _run_shell_loop(
        session=session,
        image=image,
        vql_path=vql_path,
        lang=lang,
        cfg=cfg,
        execute=execute,
        use_llm=use_llm,
        no_filter=no_filter,
        stdin=stdin,
        stdout=stdout,
        stderr=stderr,
    )


def _run_shell_loop(
    *,
    session: InteractSession,
    image: str,
    vql_path: str,
    lang: str,
    cfg: ImglConfig,
    execute: bool,
    use_llm: bool,
    no_filter: bool,
    stdin: TextIO,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    while True:
        prompt = _read_shell_prompt(stdin, stderr)
        if prompt is None:
            print("\nKoniec.", file=stdout)
            return 0
        if not prompt:
            continue

        if session.phase == "windows":
            window_action = _handle_window_phase_prompt(
                prompt,
                session=session,
                cfg=cfg,
                use_llm=use_llm,
                no_filter=no_filter,
                stdout=stdout,
                stderr=stderr,
            )
            if window_action == "quit":
                return 0
            if window_action:
                continue

        if prompt.casefold() in {"okna", "okno", "windows", "window"}:
            session.phase = "windows"
            session.selected_window_id = None
            print(format_window_picker(session.window_summaries or [], scene=session.scene), file=stdout)
            print("Wybierz okno (numer), 'podglad', 'wszystkie', 'quit'.", file=stderr)
            continue

        resolved = prompt_to_imgl_uri(
            prompt,
            image=image,
            file=vql_path,
            lang=lang,
            catalog=session.catalog,
        )
        if resolved is None:
            print("Nie rozumiem — podaj numer, 'lista', 'kliknij …', 'wpisz … w …'.", file=stdout)
            continue

        if resolved.match_reason == "quit":
            print("Koniec.", file=stdout)
            return 0

        print(f"\n→ URI ({resolved.confidence:.0%}): {resolved.uri}", file=stdout)
        result = resolve_imgl_uri(resolved.uri, session)
        _handle_resolved_shell_action(
            result=result,
            session=session,
            execute=execute,
            stdout=stdout,
        )


def describe_resolution(resolved: ResolvedImglUri) -> str:
    return f"{resolved.uri} ({resolved.match_reason}, {resolved.confidence:.0%})"


def _print_catalog_banner(
    session: InteractSession,
    cfg: ImglConfig,
    use_llm: bool,
    no_filter: bool,
    stderr: TextIO,
) -> None:
    llm_meta = getattr(build_interactive_catalog, "_last_llm_meta", None)
    window_label = session.selected_window_id or "cały ekran"
    if use_llm or cfg.use_llm_catalog:
        if llm_meta and llm_meta.get("source") == "llm":
            print(
                f"Katalog: vision LLM ({llm_meta.get('model', '')}, "
                f"okno={window_label}, {llm_meta.get('element_count', len(session.catalog))} elementów)",
                file=stderr,
            )
        else:
            err = (llm_meta or {}).get("error", "unknown error")
            print(f"UWAGA: LLM niedostępny ({err})", file=stderr)
            print("Katalog: fallback heurystyczny (filtrowany OCR)", file=stderr)
    elif not no_filter:
        print(
            f"Katalog: przefiltrowany (okno={window_label}, max {cfg.catalog_max_items} elementów)",
            file=stderr,
        )


def _handle_window_phase_prompt(
    prompt: str,
    *,
    session: InteractSession,
    cfg: ImglConfig,
    use_llm: bool,
    no_filter: bool,
    stdout: TextIO,
    stderr: TextIO,
) -> bool | str:
    lowered = prompt.casefold().strip()
    if lowered in {"quit", "exit", "wyjście", "wyjdz", "koniec"}:
        print("Koniec.", file=stdout)
        return "quit"

    if lowered in {"podglad", "podgląd", "preview", "wycinki", "crops"}:
        paths = _export_window_previews(session)
        for path in paths:
            print(f"Wycinek okna: {path}", file=stdout)
        return True

    if lowered in {"wszystkie", "all", "full", "cały", "caly", "screen"}:
        session.selected_window_id = None
        session.phase = "actions"
        session.catalog = _build_session_catalog(session)
        _print_catalog_banner(session, cfg, use_llm, no_filter, stderr)
        print(format_catalog_table(session.catalog), file=stdout)
        print("Tryb interaktywny — numer, NL, 'mapa', 'okna', 'quit'.", file=stderr)
        return True

    number_text = lowered
    for prefix in ("okno", "window", "wybierz", "select"):
        if number_text.startswith(prefix):
            number_text = number_text[len(prefix) :].strip()
            break
    if number_text.isdigit():
        if not _select_window(session, int(number_text)):
            print("Nieprawidłowy numer okna.", file=stdout)
            return True
        _print_catalog_banner(session, cfg, use_llm, no_filter, stderr)
        print(format_catalog_table(session.catalog), file=stdout)
        print("Tryb interaktywny — numer, NL, 'mapa', 'okna', 'quit'.", file=stderr)
        return True

    return False
