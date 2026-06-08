"""Tests for VQL export."""

from __future__ import annotations

import json
from pathlib import Path

from imgl.export import scene_to_vql, scene_to_vql_json, write_vql_program
from imgl.types import BBox, Element, OcrBox, Scene, Window


def _sample_scene() -> Scene:
    return Scene(
        width=400,
        height=260,
        source_image="/tmp/dialog.png",
        windows=[
            Window(
                id="win-1",
                bbox=BBox(x=20, y=20, w=360, h=220),
                title="Settings",
                z=2,
                elements=[
                    Element(
                        id="win-1-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=270, y=190, w=80, h=32),
                        confidence=0.68,
                    ),
                    Element(
                        id="win-1-input-0",
                        type="input",
                        text="tom",
                        bbox=BBox(x=150, y=84, w=190, h=30),
                        confidence=0.65,
                    ),
                ],
            )
        ],
        ocr_boxes=[
            OcrBox(text="Save", bbox=BBox(x=288, y=196, w=40, h=20), confidence=90.0),
        ],
        metadata={"roles": {"button": 1, "input": 1}, "detect_source": "local"},
    )


def test_scene_to_vql_structure():
    program = scene_to_vql(_sample_scene())
    assert program["version"] == "1.0"
    assert program["render_target"] == "svg"
    assert program["scene"]["width"] == 400.0
    assert program["metadata"]["source"] == "imgl"

    layer_ids = [layer["id"] for layer in program["scene"]["layers"]]
    assert "windows" in layer_ids
    assert "ui_elements" in layer_ids
    assert "text_regions" in layer_ids

    ui_layer = next(layer for layer in program["scene"]["layers"] if layer["id"] == "ui_elements")
    roles = {obj["metadata"]["role"] for obj in ui_layer["objects"]}
    assert "button" in roles
    assert "input" in roles

    button = next(obj for obj in ui_layer["objects"] if obj["metadata"]["role"] == "button")
    assert button["metadata"]["label"] == "Save"
    assert button["metadata"]["text"] == "Save"
    assert button["center_x"] == 310.0


def test_scene_to_vql_json_roundtrip():
    payload = scene_to_vql_json(_sample_scene())
    data = json.loads(payload)
    assert data["scene"]["height"] == 260.0
    assert data["metadata"]["by_role"]["button"] == 1


def test_write_vql_program(tmp_path):
    out = tmp_path / "layout.vql.json"
    write_vql_program(_sample_scene(), out)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["metadata"]["source"] == "imgl"


def test_cli_vql_command(tmp_path, capsys):
    from unittest.mock import MagicMock, patch

    from PIL import Image

    image_path = tmp_path / "screen.png"
    Image.new("RGB", (100, 80), color=(255, 255, 255)).save(image_path)

    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(["vql", str(image_path)])

    assert result == 0
    output = json.loads(capsys.readouterr().out)
    assert output["version"] == "1.0"
    assert output["metadata"]["source"] == "imgl"
