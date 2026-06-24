"""Decode vql://window/imgl URIs to DSL lines."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse


def _dsl_click(qs: dict, flags: str) -> str:
    text = (qs.get("text") or [""])[0]
    element_id = (qs.get("element_id") or [""])[0]
    if element_id:
        return f"RESOLVE {element_id}{flags}"
    return f'EXECUTE "kliknij {text}"{flags}'


def _dsl_type(qs: dict, flags: str) -> str:
    value = (qs.get("value") or [""])[0]
    label = (qs.get("label") or qs.get("text") or [""])[0]
    return f'TYPE "{value}" IN "{label}"{flags}'


def uri_to_dsl(uri: str) -> str:
    parsed = urlparse(uri)
    if parsed.scheme != "vql":
        raise ValueError(f"Not a vql:// URI: {uri}")
    selector = (parsed.netloc + parsed.path).strip("/")
    if selector not in {"window/imgl", "imgl"}:
        raise ValueError(f"Unsupported selector: {selector}")
    qs = parse_qs(parsed.query)
    action = (qs.get("action") or ["list"])[0].lower()
    image = (qs.get("image") or ["screen.png"])[0]
    window = (qs.get("window") or [""])[0] or None
    flags = f" IMAGE {image}" + (f" WINDOW {window}" if window else "")

    if action == "list":
        return f"ACTIONS {image}{flags.replace(' IMAGE ' + image, '')}"
    if action == "analyze":
        return f"ANALYZE {image}{flags.replace(' IMAGE ' + image, '')}"
    if action == "click":
        return _dsl_click(qs, flags)
    if action == "type":
        return _dsl_type(qs, flags)
    return f"RESOLVE {uri}"
