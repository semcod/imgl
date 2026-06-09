"""Heuristic (OCR/geometry) interactive catalog builder — no LLM dependency."""

from __future__ import annotations

from imgl.actions import ActionTarget, SceneActions, actions
from imgl.catalog_types import InteractiveOption
from imgl.types import Element, Scene, Window
from imgl.uri import uri_for_imgl_click


def build_heuristic_catalog(
    scene: Scene,
    *,
    image_path: str,
    vql_file: str = "layout.vql.json",
    lang: str = "eng",
    filter_noise: bool = True,
    max_items: int = 40,
    window_id: str | None = None,
    include_window_entries: bool = True,
) -> list[InteractiveOption]:
    """Enumerate windows, buttons, and inputs from scene detection (no LLM)."""
    scoped_window = _find_window(scene, window_id) if window_id else None

    options: list[InteractiveOption] = []
    index = 1

    if include_window_entries and scoped_window is None:
        for window in scene.windows:
            options.append(
                _window_option(index, window, image_path=image_path, vql_file=vql_file, lang=lang)
            )
            index += 1

    finder = actions(scene)
    seen_ids: set[str] = {opt.element_id for opt in options}

    for win, element in _iter_interactive_elements(scene, window_id=window_id):
        if element.id in seen_ids:
            continue
        option = _element_option(
            index,
            element,
            window=win,
            finder=finder,
            image_path=image_path,
            vql_file=vql_file,
            lang=lang,
        )
        if option is not None:
            options.append(option)
            seen_ids.add(element.id)
            index += 1

    if filter_noise:
        from imgl.catalog_filter import filter_catalog

        return filter_catalog(options, max_items=max_items)

    return options


def infer_input_label(element: Element, window: Window | None) -> str:
    """Guess a human label for geometry-only input frames (no OCR placeholder)."""
    rel_y = element.bbox.y - (window.bbox.y if window else 0)
    width = element.bbox.w
    height = element.bbox.h
    if width >= 280 and height <= 70 and rel_y >= 900:
        return "Chat input"
    if width >= 200 and height <= 50 and rel_y >= 1100:
        return "Terminal"
    if width >= 350 and height <= 90 and rel_y <= 250:
        return "Editor"
    if width >= 120 and height <= 60:
        return "Pole tekstowe"
    return "Input"


def _window_option(
    index: int,
    window: Window,
    *,
    image_path: str,
    vql_file: str,
    lang: str,
) -> InteractiveOption:
    title = window.title or window.id
    cx = window.bbox.x + window.bbox.w // 2
    cy = window.bbox.y + min(20, window.bbox.h // 2)
    payload = {
        "action": "click",
        "x": cx,
        "y": cy,
        "element_id": window.id,
        "element_type": "window",
        "text": title,
        "window_id": window.id,
        "bbox": window.bbox.to_dict(),
    }
    return InteractiveOption(
        index=index,
        category="window",
        element_id=window.id,
        element_type="window",
        label=title,
        text=title,
        window_id=window.id,
        window_title=title,
        position=(cx, cy),
        bbox=window.bbox.to_dict(),
        mouse_actions=[f"LPM na pasku tytułu ({cx}, {cy}) — aktywuj okno"],
        keyboard_actions=["Alt+Tab — przełącz okno", "Super+` — następne okno (GNOME)"],
        primary_action="click",
        action_uri=uri_for_imgl_click(
            image=image_path,
            file=vql_file,
            window=window.id,
            lang=lang,
        ),
        action_payload=payload,
    )


def _element_option(
    index: int,
    element: Element,
    *,
    window: Window | None,
    finder: SceneActions,
    image_path: str,
    vql_file: str,
    lang: str,
) -> InteractiveOption | None:
    target = ActionTarget(element=element, window=window)
    x, y = target.click_coords()
    window_id = window.id if window else None
    window_title = window.title if window else None
    label = element.metadata.get("label") or element.text or element.id

    if element.type in {"button", "icon_button"}:
        payload = target.to_click_action()
        return InteractiveOption(
            index=index,
            category="button",
            element_id=element.id,
            element_type=element.type,
            label=label,
            text=element.text,
            window_id=window_id,
            window_title=window_title,
            position=(x, y),
            bbox=element.bbox.to_dict(),
            mouse_actions=[f"LPM ({x}, {y}) — kliknij"],
            keyboard_actions=["Tab do elementu + Enter", "Spacja gdy fokus na przycisku"],
            primary_action="click",
            action_uri=uri_for_imgl_click(
                image=image_path,
                file=vql_file,
                text=element.text or None,
                element_id=element.id,
                window=window_id,
                lang=lang,
            ),
            action_payload=payload,
        )

    if element.type == "input":
        input_label = element.metadata.get("label") or infer_input_label(element, window)
        click_payload = target.to_click_action()
        click_payload["element_type"] = "input"
        if input_label:
            click_payload["label"] = input_label
        field_name = str(input_label or label)
        return InteractiveOption(
            index=index,
            category="input",
            element_id=element.id,
            element_type="input",
            label=field_name,
            text=element.text,
            window_id=window_id,
            window_title=window_title,
            position=(x, y),
            bbox=element.bbox.to_dict(),
            mouse_actions=[f"LPM ({x}, {y}) — ustaw fokus w polu"],
            keyboard_actions=[
                f"wpisz TEKST w {field_name!r} — wpisanie tekstu",
                "numer opcji — samo ustawienie fokusu (klik)",
            ],
            primary_action="click",
            action_uri=uri_for_imgl_click(
                image=image_path,
                file=vql_file,
                label=str(input_label) if input_label else None,
                element_id=element.id,
                window=window_id,
                lang=lang,
            ),
            action_payload=click_payload,
        )

    if element.type == "toolbar":
        payload = target.to_click_action()
        return InteractiveOption(
            index=index,
            category="toolbar",
            element_id=element.id,
            element_type=element.type,
            label=label,
            text=element.text,
            window_id=window_id,
            window_title=window_title,
            position=(x, y),
            bbox=element.bbox.to_dict(),
            mouse_actions=[f"LPM ({x}, {y}) — aktywuj pasek narzędzi"],
            keyboard_actions=["Skróty aplikacji zależą od kontekstu"],
            primary_action="click",
            action_uri=uri_for_imgl_click(
                image=image_path,
                file=vql_file,
                element_id=element.id,
                window=window_id,
                lang=lang,
            ),
            action_payload=payload,
        )

    return None


def _find_window(scene: Scene, window_id: str | None) -> Window | None:
    if not window_id:
        return None
    from imgl.window_scope import get_discovered_window

    return get_discovered_window(scene, window_id)


def _iter_interactive_elements(
    scene: Scene,
    *,
    window_id: str | None = None,
) -> list[tuple[Window | None, Element]]:
    pairs: list[tuple[Window | None, Element]] = []
    interactive = {"button", "icon_button", "input", "toolbar"}
    for window in scene.windows:
        if window_id and window.id != window_id:
            continue
        for element in window.elements:
            if element.type in interactive:
                pairs.append((window, element))
    if not window_id:
        for element in scene.orphan_elements:
            if element.type in interactive:
                pairs.append((None, element))
    return pairs
