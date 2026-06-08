"""Tests for OCR language normalization."""

from __future__ import annotations

from imgl.ocr.lang import normalize_ocr_lang, ocr_lang_attempts


def test_normalize_url_decoded_lang():
    assert normalize_ocr_lang("eng pol") == "eng+pol"
    assert normalize_ocr_lang("eng+pol") == "eng+pol"


def test_ocr_lang_attempts_fallback():
    attempts = ocr_lang_attempts("eng pol")
    assert attempts[0] == "eng+pol"
    assert "eng" in attempts
