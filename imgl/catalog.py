"""Build interactive option catalogs from analyzed scenes."""

from __future__ import annotations

from imgl.catalog_heuristic import build_heuristic_catalog, infer_input_label
from imgl.catalog_types import InteractiveOption
from imgl.types import Scene

# Backward-compatible alias for lazy imports in actions.py.
_infer_input_label = infer_input_label


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
    if use_llm:
        from imgl.llm_catalog import refine_catalog_with_llm

        scoped_window = None
        if window_id:
            from imgl.catalog_heuristic import _find_window

            scoped_window = _find_window(scene, window_id)

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

    return build_heuristic_catalog(
        scene,
        image_path=image_path,
        vql_file=vql_file,
        lang=lang,
        filter_noise=filter_noise,
        max_items=max_items,
        window_id=window_id,
        include_window_entries=include_window_entries,
    )


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


def _truncate(value: str, max_len: int) -> str:
    text = value.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"
