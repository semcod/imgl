"""OCR language string normalization."""

from __future__ import annotations


def normalize_ocr_lang(lang: str) -> str:
    """
    Normalize Tesseract language codes.

    URL query strings decode ``+`` as space, so ``eng+pol`` becomes ``eng pol``.
    """
    cleaned = (lang or "eng").strip()
    if not cleaned:
        return "eng"
    return cleaned.replace(" ", "+")


def ocr_lang_attempts(lang: str) -> list[str]:
    """Return language codes to try, in order."""
    primary = normalize_ocr_lang(lang)
    attempts = [primary]
    if primary != "eng":
        attempts.append("eng")
    if "+" in primary:
        attempts.append(primary.split("+", 1)[0])
    seen: set[str] = set()
    ordered: list[str] = []
    for item in attempts:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
