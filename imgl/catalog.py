"""Build interactive option catalogs from analyzed scenes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from imgl.actions import ActionTarget, SceneActions, actions
from imgl.types import Element, Scene, Window
from imgl.uri import uri_for_imgl_click, uri_for_imgl_list, uri_for_imgl_type


@dataclass
class InteractiveOption:
    """One selectable UI target with mouse/keyboard affordances."""

    index: int
    category: str
    element_id: str
    element_type: str
    label: str
    text: str | None
    window_id: str | None
    window_title: str | None
    position: tuple[int, int]
    bbox: dict[str, int]
    mouse_actions: list[str] = field(default_factory=list)
    keyboard_actions: list[str] = field(default_factory=list)
    primary_action: str = "click"
    action_uri: str = ""
    action_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "category": self.category,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "label": self.label,
            "text": self.text,
            "window_id": self.window_id,
            "window_title": self.window_title,
            "position": {"x": self.position[0], "y": self.position[1]},
            "bbox": self.bbox,
            "mouse_actions": self.mouse_actions,
            "keyboard_actions": self.keyboard_actions,
            "primary_action": self.primary_action,
            "action_uri": self.action_uri,
            "action_payload": self.action_payload,
        }


def build_interactive_catalog(
    scene: Scene,
    *,
    image_path: str,
    vql_file: str = "layout.vql.json",
    lang: str = "eng",
    filter_noise: bool = True,
    use_llm: bool = False,
    llm_model: str | None = None,
    max_items: int = 40,
    window_id: str | None = None,
    include_window_entries: bool = True,
) -> list[InteractiveOption]:
    """Enumerate windows, buttons, and inputs with actionable URIs."""
    scoped_window = _find_window(scene, window_id) if window_id else None

    if use_llm:
        from imgl.llm_catalog import refine_catalog_with_llm

        options, meta = refine_catalog_with_llm(
            scene,
            image_path=image_path,
            vql_file=vql_file,
            lang=lang,
            model=llm_model,
            max_elements=max_items,
            window=scoped_window,
        )
        build_interactive_catalog._last_llm_meta = meta  # type: ignore[attr-defined]
        return options

    options: list[InteractiveOption] = []
    index = 1

    windows = [scoped_window] if scoped_window is not None else list(scene.windows)
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


def format_catalog_table(options: list[InteractiveOption]) -> str:
    """Human-readable numbered list for the interactive shell."""
    if not options:
        return "Brak wykrytych elementów interaktywnych."

    lines = ["", "=== Elementy interaktywne (mysz / klawiatura) ===", ""]
    current_category = ""
    for opt in options:
        if opt.category != current_category:
            current_category = opt.category
            lines.append(f"[{current_category.upper()}]")
        text = opt.text or opt.label
        text_part = f' "{_truncate(text, 48)}"' if text else ""
        lines.append(
            f"  {opt.index:3d}. {opt.element_type}{text_part} "
            f"@ ({opt.position[0]}, {opt.position[1]})"
        )
        if opt.mouse_actions:
            lines.append(f"       mysz: {opt.mouse_actions[0]}")
        if opt.keyboard_actions:
            lines.append(f"       klawiatura: {opt.keyboard_actions[0]}")
    lines.append("")
    lines.append("Wpisz numer opcji, 'mapa' (obraz z numerami), lub NL (nlp2uri).")
    lines.append("")
    return "\n".join(lines)


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
        input_label = element.metadata.get("label")
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


def _truncate(value: str, max_len: int) -> str:
    text = value.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
