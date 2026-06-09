"""Natural language → vql://window/imgl URI for screen control."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from imgl.catalog import InteractiveOption
from imgl.uri import (
    uri_for_imgl_analyze,
    uri_for_imgl_annotate,
    uri_for_imgl_click,
    uri_for_imgl_list,
    uri_for_imgl_type,
)


@dataclass(frozen=True)
class ResolvedImglUri:
    uri: str
    confidence: float
    match_reason: str
    action_payload: dict[str, Any] | None = None
    option_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "uri": self.uri,
            "confidence": self.confidence,
            "match_reason": self.match_reason,
            "action_payload": self.action_payload,
            "option_index": self.option_index,
        }


_NUMBER_RE = re.compile(
    r"^(?:wybierz|select|option|opcja|numer|#|nr\.?)?\s*(\d+)\s*$",
    re.IGNORECASE,
)
_CLICK_RE = re.compile(
    r"\b(kliknij|click|naciśnij|nacisnij|press|tap|otwórz|otworz|open)\b\s+(.+)",
    re.IGNORECASE,
)
_TYPE_RE = re.compile(
    r'^(?:wpisz|wprowadź|wprowadz|enter|wpisz tekst)\b\s+["\']?([^"\']+?)["\']?'
    r"(?:\s+(?:w|in|do|into|pole|field)\s+(.+))?\s*$",
    re.IGNORECASE,
)
_TYPE_EN_RE = re.compile(
    r'^type\s+["\']?([^"\']+?)["\']?'
    r"(?:\s+(?:in|into|field)\s+(.+))?\s*$",
    re.IGNORECASE,
)
_LIST_RE = re.compile(
    r"\b(lista|list|pokaż|pokaz|show|elementy|elements|opcje|options|menu)\b",
    re.IGNORECASE,
)
_MAP_RE = re.compile(
    r"\b(mapa|mapę|mape|map|obraz|image|annotat|numeruj|numeracja|numerów|numerow|"
    r"podgląd|podglad|preview|oznacz)\b",
    re.IGNORECASE,
)
_ANALYZE_RE = re.compile(
    r"\b(przeanalizuj|analizuj|analyze|odśwież|odswiez|refresh|layout|układ|uklad)\b",
    re.IGNORECASE,
)
_QUIT_RE = re.compile(r"\b(wyjście|wyjdz|quit|exit|koniec|stop)\b", re.IGNORECASE)


def prompt_to_imgl_uri(
    prompt: str,
    *,
    image: str,
    file: str = "layout.vql.json",
    lang: str = "eng",
    catalog: list[InteractiveOption] | None = None,
) -> ResolvedImglUri | None:
    """Map natural language or numeric selection to imgl vql:// URI."""
    text = prompt.strip()
    if not text:
        return None

    number_match = _NUMBER_RE.match(text)
    if number_match and catalog:
        idx = int(number_match.group(1))
        for option in catalog:
            if option.index == idx:
                return ResolvedImglUri(
                    uri=option.action_uri,
                    confidence=1.0,
                    match_reason="catalog:index",
                    action_payload=option.action_payload,
                    option_index=idx,
                )
        return None

    if _QUIT_RE.search(text):
        return ResolvedImglUri(
            uri="vql://window/imgl?action=quit",
            confidence=1.0,
            match_reason="quit",
        )

    if _MAP_RE.search(text):
        return ResolvedImglUri(
            uri=uri_for_imgl_annotate(image=image, file=file, lang=lang),
            confidence=0.96,
            match_reason="annotate",
        )

    if _LIST_RE.search(text):
        return ResolvedImglUri(
            uri=uri_for_imgl_list(image=image, file=file, lang=lang),
            confidence=0.95,
            match_reason="list",
        )

    if _ANALYZE_RE.search(text):
        return ResolvedImglUri(
            uri=uri_for_imgl_analyze(image=image, file=file, lang=lang),
            confidence=0.9,
            match_reason="analyze",
        )

    click_match = _CLICK_RE.search(text)
    if click_match:
        target_text = click_match.group(2).strip().strip('"\'')
        payload = None
        option_index = None
        if catalog:
            matched = _find_catalog_by_text(catalog, target_text)
            if matched:
                payload = matched.action_payload
                option_index = matched.index
                return ResolvedImglUri(
                    uri=matched.action_uri,
                    confidence=0.93,
                    match_reason="catalog:text",
                    action_payload=payload,
                    option_index=option_index,
                )
        return ResolvedImglUri(
            uri=uri_for_imgl_click(
                image=image,
                file=file,
                text=target_text,
                lang=lang,
            ),
            confidence=0.8,
            match_reason="click",
            action_payload=payload,
            option_index=option_index,
        )

    type_match = _TYPE_RE.match(text) or _TYPE_EN_RE.match(text)
    if type_match:
        value = type_match.group(1).strip()
        field_hint = (type_match.group(2) or "").strip() or None
        matched_input = _find_catalog_input(catalog, field_hint) if catalog and field_hint else None
        payload = None
        if matched_input:
            payload = dict(matched_input.action_payload)
            payload["action"] = "type"
            payload["text"] = value
        return ResolvedImglUri(
            uri=uri_for_imgl_type(
                image=image,
                file=file,
                value=value,
                label=field_hint,
                text=matched_input.label if matched_input else None,
                element_id=matched_input.element_id if matched_input else None,
                window=matched_input.window_id if matched_input else None,
                lang=lang,
            ),
            confidence=0.95 if matched_input else (0.92 if field_hint else 0.75),
            match_reason="type",
            action_payload=payload,
            option_index=matched_input.index if matched_input else None,
        )

    if catalog:
        fuzzy = _find_catalog_by_text(catalog, text)
        if fuzzy:
            return ResolvedImglUri(
                uri=fuzzy.action_uri,
                confidence=0.7,
                match_reason="catalog:fuzzy",
                action_payload=fuzzy.action_payload,
                option_index=fuzzy.index,
            )

    return _delegate_vql_nlp2uri(
        text,
        image=image,
        file=file,
        lang=lang,
    )


def _delegate_vql_nlp2uri(
    prompt: str,
    *,
    image: str,
    file: str,
    lang: str,
) -> ResolvedImglUri | None:
    try:
        from uri2vql.nlp2uri import best_uri

        hit = best_uri(prompt, file=file, image=image)
        if hit:
            return ResolvedImglUri(
                uri=hit.uri,
                confidence=hit.confidence,
                match_reason=f"vql:{hit.match_reason}",
            )
    except ImportError:
        pass

    lowered = prompt.casefold()
    if any(word in lowered for word in ("klik", "click", "button", "przycisk")):
        return ResolvedImglUri(
            uri=uri_for_imgl_list(image=image, file=file, lang=lang),
            confidence=0.4,
            match_reason="fallback:list",
        )
    return None


def _find_catalog_by_text(
    catalog: list[InteractiveOption],
    query: str,
) -> InteractiveOption | None:
    query_cf = query.casefold()
    for option in catalog:
        for candidate in (option.text, option.label, option.element_id):
            if candidate and query_cf in candidate.casefold():
                return option
    for option in catalog:
        for candidate in (option.text, option.label):
            if candidate and candidate.casefold() in query_cf:
                return option
    return None


def _find_catalog_input(
    catalog: list[InteractiveOption],
    hint: str,
) -> InteractiveOption | None:
    hint_cf = hint.casefold().strip()
    if not hint_cf:
        return None
    for option in catalog:
        if option.category != "input":
            continue
        for candidate in (option.label, option.text):
            if not candidate:
                continue
            cand_cf = candidate.casefold().strip()
            if hint_cf == cand_cf or hint_cf in cand_cf or cand_cf in hint_cf:
                return option
    return None


def _match_catalog_action(
    catalog: list[InteractiveOption],
    hint: str,
    *,
    action: str,
) -> dict[str, Any] | None:
    if action == "type":
        matched = _find_catalog_input(catalog, hint)
        return matched.action_payload if matched else None
    for option in catalog:
        if option.primary_action != action:
            continue
        label = (option.label or "").casefold()
        if hint.casefold() in label or label in hint.casefold():
            return option.action_payload
    return None
