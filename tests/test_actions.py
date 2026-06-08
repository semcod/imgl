"""Tests for scene actions."""

from __future__ import annotations

import json
import pytest

from imgl.actions import ElementNotFoundError, SceneActions, actions
from imgl.types import BBox, Element, Scene, Window


def _dialog_scene() -> Scene:
    return Scene(
        width=400,
        height=260,
        windows=[
            Window(
                id="win-settings",
                bbox=BBox(x=20, y=20, w=360, h=220),
                title="Settings",
                z=2,
                elements=[
                    Element(
                        id="win-settings-label-0",
                        type="label",
                        text="Username",
                        bbox=BBox(x=40, y=90, w=90, h=20),
                        metadata={"for_input": "win-settings-input-0"},
                    ),
                    Element(
                        id="win-settings-input-0",
                        type="input",
                        text="tom",
                        bbox=BBox(x=150, y=84, w=190, h=30),
                        metadata={"label": "Username"},
                    ),
                    Element(
                        id="win-settings-button-0",
                        type="button",
                        text="Save",
                        bbox=BBox(x=270, y=190, w=80, h=32),
                    ),
                    Element(
                        id="win-settings-button-1",
                        type="button",
                        text="Cancel",
                        bbox=BBox(x=180, y=190, w=80, h=32),
                    ),
                ],
            )
        ],
    )


def test_find_button_by_text():
    finder = actions(_dialog_scene())
    matches = finder.find("button", text="Save")
    assert len(matches) == 1
    assert matches[0].element.text == "Save"


def test_find_input_by_label():
    finder = actions(_dialog_scene())
    match = finder.find_one("input", label="Username")
    assert match is not None
    assert match.element.text == "tom"


def test_click_coords():
    finder = actions(_dialog_scene())
    target = finder.find_one("button", text="Save")
    assert target is not None
    assert target.click_coords() == (310, 206)


def test_click_action():
    finder = actions(_dialog_scene())
    action = finder.click("button", text="Save")
    assert action["action"] == "click"
    assert action["x"] == 310
    assert action["y"] == 206
    assert action["element_type"] == "button"
    assert action["window_id"] == "win-settings"


def test_type_into_by_label():
    finder = actions(_dialog_scene())
    action = finder.type_into("alice", label="Username")
    assert action["action"] == "type"
    assert action["text"] == "alice"
    assert action["label"] == "Username"
    assert action["x"] == 245
    assert action["y"] == 99


def test_find_in_window():
    finder = actions(_dialog_scene())
    matches = finder.find("button", window="Settings")
    assert len(matches) == 2


def test_find_one_not_found():
    finder = actions(_dialog_scene())
    assert finder.find_one("button", text="Delete") is None


def test_click_raises_when_missing():
    finder = actions(_dialog_scene())
    with pytest.raises(ElementNotFoundError, match="text='Delete'"):
        finder.click("button", text="Delete")


def test_list_actions():
    finder = actions(_dialog_scene())
    listed = finder.list_actions()
    assert len(listed) == 3
    kinds = {item["action"] for item in listed}
    assert kinds == {"click", "type"}


def test_cli_find_command(tmp_path, capsys):
    from unittest.mock import MagicMock, patch

    from PIL import Image

    image_path = tmp_path / "screen.png"
    Image.new("RGB", (100, 80), color=(255, 255, 255)).save(image_path)

    mock_backend = MagicMock()
    mock_backend.run.return_value = []

    with patch("imgl.pipeline.get_ocr_backend", return_value=mock_backend):
        from imgl.cli import main

        result = main(["find", str(image_path), "--list"])

    assert result == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
