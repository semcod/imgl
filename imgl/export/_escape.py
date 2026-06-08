"""HTML/XML escaping helpers."""

from __future__ import annotations

import html


def escape_html(text: str) -> str:
    return html.escape(text, quote=True)


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
