"""vql:// URI builders for imgl screen-control DSL."""

from __future__ import annotations

from urllib.parse import urlencode

VQL_SCHEME = "vql"
IMGL_SELECTOR = "window/imgl"


def _imgl_uri(
    *,
    image: str,
    file: str,
    extra: dict[str, str | int | float] | None = None,
) -> str:
    params: dict[str, str] = {
        "image": image,
        "file": file,
    }
    if extra:
        for key, value in extra.items():
            if value != "" and value is not None:
                params[key] = str(value)
    return f"{VQL_SCHEME}://{IMGL_SELECTOR}?{urlencode(params)}"


def uri_for_imgl_analyze(
    *,
    image: str,
    file: str = "layout.vql.json",
    lang: str = "eng",
    with_grid: bool = False,
    grid: int = 12,
) -> str:
    extra: dict[str, str | int] = {"action": "analyze", "lang": lang, "grid": grid}
    if with_grid:
        extra["with_grid"] = "1"
    return _imgl_uri(image=image, file=file, extra=extra)


def uri_for_imgl_annotate(
    *,
    image: str,
    file: str = "layout.vql.json",
    lang: str = "eng",
    output: str = "",
) -> str:
    extra: dict[str, str] = {"action": "annotate", "lang": lang}
    if output:
        extra["output"] = output
    return _imgl_uri(image=image, file=file, extra=extra)


def uri_for_imgl_list(
    *,
    image: str,
    file: str = "layout.vql.json",
    lang: str = "eng",
) -> str:
    return _imgl_uri(image=image, file=file, extra={"action": "list", "lang": lang})


def uri_for_imgl_click(
    *,
    image: str,
    file: str = "layout.vql.json",
    text: str | None = None,
    label: str | None = None,
    element_id: str | None = None,
    window: str | None = None,
    lang: str = "eng",
) -> str:
    extra: dict[str, str] = {"action": "click", "lang": lang}
    if text:
        extra["text"] = text
    if label:
        extra["label"] = label
    if element_id:
        extra["element_id"] = element_id
    if window:
        extra["window"] = window
    return _imgl_uri(image=image, file=file, extra=extra)


def uri_for_imgl_type(
    *,
    image: str,
    file: str = "layout.vql.json",
    value: str,
    label: str | None = None,
    text: str | None = None,
    element_id: str | None = None,
    window: str | None = None,
    lang: str = "eng",
) -> str:
    extra: dict[str, str] = {"action": "type", "value": value, "lang": lang}
    if label:
        extra["label"] = label
    if text:
        extra["text"] = text
    if element_id:
        extra["element_id"] = element_id
    if window:
        extra["window"] = window
    return _imgl_uri(image=image, file=file, extra=extra)


def uri_for_imgl_action(
    *,
    image: str,
    file: str = "layout.vql.json",
    action: str,
    lang: str = "eng",
    **params: str,
) -> str:
    extra: dict[str, str] = {"action": action, "lang": lang, **params}
    return _imgl_uri(image=image, file=file, extra=extra)
