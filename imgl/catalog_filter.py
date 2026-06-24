"""Filter noisy OCR/heuristic detections from interactive catalogs."""

from __future__ import annotations

import re

from imgl.catalog_types import InteractiveOption

_CODE_RE = re.compile(
    r"(import\s|from\s+\w+\s+import|def\s|class\s|window_\d+-|"
    r'"\w+":\s*|{\s*$|}\s*$|^\s*#|^\s*//|^\s*\.\.\.)',
    re.IGNORECASE,
)
_GENERIC_ID_RE = re.compile(r"^window_\d+-(button|input)-\d+$", re.IGNORECASE)
_SYMBOL_HEAVY_RE = re.compile(r"^[\W_\d]{3,}$")


def filter_catalog(
    options: list[InteractiveOption],
    *,
    max_items: int = 40,
    min_width: int = 28,
    min_height: int = 16,
    max_button_chars: int = 48,
) -> list[InteractiveOption]:
    """Drop obvious false positives and renumber surviving options."""
    kept: list[tuple[float, InteractiveOption]] = []

    for option in options:
        if option.category == "window":
            kept.append((_window_score(option), option))
            continue

        if not _keep_element(
            option,
            min_width=min_width,
            min_height=min_height,
            max_button_chars=max_button_chars,
        ):
            continue
        kept.append((_element_score(option), option))

    kept.sort(key=lambda pair: (-pair[0], pair[1].position[1], pair[1].position[0]))
    windows = [opt for score, opt in kept if opt.category == "window"]
    others = [opt for score, opt in kept if opt.category != "window"][:max_items]
    ordered = windows + others
    return _renumber(ordered)


def _renumber(options: list[InteractiveOption]) -> list[InteractiveOption]:
    renumbered: list[InteractiveOption] = []
    for index, option in enumerate(options, start=1):
        renumbered.append(
            InteractiveOption(
                index=index,
                category=option.category,
                element_id=option.element_id,
                element_type=option.element_type,
                label=option.label,
                text=option.text,
                window_id=option.window_id,
                window_title=option.window_title,
                position=option.position,
                bbox=option.bbox,
                mouse_actions=option.mouse_actions,
                keyboard_actions=option.keyboard_actions,
                primary_action=option.primary_action,
                action_uri=_replace_index_in_uri(option.action_uri, index),
                action_payload=option.action_payload,
            )
        )
    return renumbered


def _replace_index_in_uri(uri: str, _index: int) -> str:
    return uri


def _text_quality_check(
    text: str,
    element_id: str,
    category: str,
    max_button_chars: int,
) -> bool:
    if not text or text == element_id:
        return False
    if _SYMBOL_HEAVY_RE.match(text):
        return False
    if _CODE_RE.search(text):
        return False
    if category == "button" and len(text) > max_button_chars:
        return False
    if category == "input" and len(text) > 80:
        return False
    alpha = sum(ch.isalnum() for ch in text)
    return alpha >= max(2, len(text) // 4)


def _keep_element(
    option: InteractiveOption,
    *,
    min_width: int,
    min_height: int,
    max_button_chars: int,
) -> bool:
    bbox = option.bbox
    if bbox.get("w", 0) < min_width or bbox.get("h", 0) < min_height:
        return False

    text = (option.text or option.label or "").strip()
    if _GENERIC_ID_RE.match(text) or _GENERIC_ID_RE.match(option.label):
        return False

    return _text_quality_check(text, option.element_id, option.category, max_button_chars)


def _element_score(option: InteractiveOption) -> float:
    text = (option.text or option.label or "").strip()
    score = 0.0
    if text and not _GENERIC_ID_RE.match(text):
        score += 2.0
    if option.category == "button":
        score += 1.5
    if option.category == "input":
        score += 1.0
    if 4 <= len(text) <= 32:
        score += 1.0
    bbox = option.bbox
    area = bbox.get("w", 0) * bbox.get("h", 0)
    if 800 <= area <= 80_000:
        score += 0.5
    return score


def _window_score(option: InteractiveOption) -> float:
    title = (option.text or option.label or "").strip()
    if title and title != "window_0":
        return 3.0
    return 2.0
