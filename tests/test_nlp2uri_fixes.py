"""Regression tests for nlp2uri click/type parsing."""

from __future__ import annotations

from imgl.catalog import InteractiveOption, build_interactive_catalog
from imgl.nlp2uri import prompt_to_imgl_uri
from imgl.types import BBox, Element, Scene, Window


def _scene_with_search_input() -> Scene:
    return Scene(
        width=400,
        height=260,
        source_image="/tmp/dialog.png",
        windows=[
            Window(
                id="win-app",
                bbox=BBox(x=0, y=0, w=400, h=260),
                title="App",
                z=1,
                elements=[
                    Element(
                        id="win-app-input-0",
                        type="input",
                        text="",
                        bbox=BBox(x=150, y=40, w=200, h=30),
                        metadata={"label": "Type to search"},
                    ),
                ],
            )
        ],
    )


def test_click_before_type_for_type_to_search_label():
    scene = _scene_with_search_input()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    resolved = prompt_to_imgl_uri(
        "kliknij Type to search",
        image="/tmp/dialog.png",
        catalog=catalog,
    )
    assert resolved is not None
    assert resolved.match_reason.startswith("catalog")
    assert resolved.action_payload is not None
    assert resolved.action_payload["action"] == "click"


def test_type_into_search_field_from_catalog():
    scene = _scene_with_search_input()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    resolved = prompt_to_imgl_uri(
        "wpisz hello w Type to search",
        image="/tmp/dialog.png",
        catalog=catalog,
    )
    assert resolved is not None
    assert resolved.match_reason == "type"
    assert "value=hello" in resolved.uri
    assert resolved.action_payload is not None
    assert resolved.action_payload["action"] == "type"
    assert resolved.action_payload["text"] == "hello"
