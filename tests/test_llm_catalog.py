"""Tests for LLM catalog helpers."""

from __future__ import annotations

import os
from pathlib import Path

from imgl.llm_catalog import (
    _env_file_candidates,
    _load_env_files,
    _merge_heuristic_inputs,
    _snap_options_to_scene,
)
from imgl.catalog import InteractiveOption, build_interactive_catalog
from imgl.types import BBox, Element, Scene, Window


def test_load_env_files_reads_dotenv(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    (tmp_path / ".env").write_text('OPENROUTER_API_KEY="sk-test-123"\n', encoding="utf-8")
    assert _env_file_candidates()[0] == tmp_path / ".env"
    _load_env_files()
    assert os.getenv("OPENROUTER_API_KEY") == "sk-test-123"


def test_snap_options_to_scene():
    scene = Scene(
        width=800,
        height=600,
        source_image="/tmp/screen.png",
        windows=[
            Window(
                id="window_0",
                bbox=BBox(x=0, y=0, w=800, h=600),
                title="App",
                z=1,
                elements=[
                    Element(
                        id="window_0-button-0",
                        type="button",
                        text="Follow",
                        bbox=BBox(x=700, y=100, w=80, h=32),
                    ),
                ],
            )
        ],
    )
    llm_option = InteractiveOption(
        index=1,
        category="button",
        element_id="llm-1",
        element_type="button",
        label="Follow",
        text="Follow",
        window_id=None,
        window_title=None,
        position=(100, 100),
        bbox={"x": 60, "y": 86, "w": 80, "h": 28},
        action_uri="vql://test",
        action_payload={"action": "click", "x": 100, "y": 100},
    )
    snapped = _snap_options_to_scene([llm_option], scene)
    assert snapped[0].element_id == "window_0-button-0"
    assert snapped[0].position == (740, 116)


def test_merge_heuristic_inputs_appends_missing_fields():
    scene = Scene(
        width=800,
        height=600,
        source_image="/tmp/screen.png",
        windows=[
            Window(
                id="region-bottom",
                bbox=BBox(x=0, y=300, w=800, h=300),
                title="IDE",
                z=1,
                elements=[
                    Element(
                        id="region-bottom-input-0",
                        type="input",
                        text=None,
                        bbox=BBox(x=100, y=520, w=400, h=36),
                    ),
                    Element(
                        id="region-bottom-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=50, y=320, w=80, h=32),
                    ),
                ],
            )
        ],
    )
    llm_only = [
        InteractiveOption(
            index=1,
            category="button",
            element_id="llm-1",
            element_type="button",
            label="Save",
            text="Save",
            window_id="region-bottom",
            window_title="IDE",
            position=(90, 336),
            bbox={"x": 50, "y": 320, "w": 80, "h": 32},
            action_uri="vql://test",
            action_payload={"action": "click", "x": 90, "y": 336},
        )
    ]
    merged = _merge_heuristic_inputs(
        llm_only,
        scene,
        image_path="/tmp/screen.png",
        vql_file="layout.vql.json",
        lang="eng",
        window=scene.windows[0],
    )
    inputs = [opt for opt in merged if opt.category == "input"]
    assert len(inputs) >= 1
    assert any(
        term in (opt.label or "")
        for opt in inputs
        for term in ("Chat", "Terminal", "Pole", "Editor", "Input")
    )
