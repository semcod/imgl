"""Tests for LLM flag in nlp2imgl.to_dsl."""

from __future__ import annotations

import pytest

nlp2imgl_to_dsl = pytest.importorskip("nlp2imgl.to_dsl")
to_dsl = nlp2imgl_to_dsl.to_dsl
use_llm_enabled = nlp2imgl_to_dsl.use_llm_enabled


def test_to_dsl_adds_llm_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMGL_USE_LLM", "1")
    line = to_dsl("wpisz test w Chat input", image="a.png", window="region-bottom")
    assert " LLM" in line
    assert "TYPE" in line


def test_to_dsl_explicit_llm_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMGL_USE_LLM", "1")
    line = to_dsl("wpisz test w Chat input", use_llm=False)
    assert " LLM" not in line


def test_use_llm_from_openrouter_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IMGL_USE_LLM", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
    assert use_llm_enabled() is True
