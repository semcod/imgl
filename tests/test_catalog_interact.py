"""Tests for interactive catalog, nlp2uri, and URI resolution."""

from __future__ import annotations

import io

from imgl.catalog import build_interactive_catalog, format_catalog_table
from imgl.interact import InteractSession, resolve_imgl_uri, run_interactive_shell
from imgl.nlp2uri import prompt_to_imgl_uri
from imgl.types import BBox, Element, Scene, Window
from imgl.uri import uri_for_imgl_click, uri_for_imgl_list, uri_for_imgl_type


def _dialog_scene() -> Scene:
    return Scene(
        width=400,
        height=260,
        source_image="/tmp/dialog.png",
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
                ],
            )
        ],
    )


def test_build_interactive_catalog():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(
        scene,
        image_path="/tmp/dialog.png",
        vql_file="layout.vql.json",
    )
    assert len(catalog) == 3
    assert catalog[0].category == "window"
    assert any(opt.text == "Save" for opt in catalog)
    inputs = [opt for opt in catalog if opt.category == "input"]
    assert inputs
    assert inputs[0].primary_action == "click"
    assert "action=click" in inputs[0].action_uri


def test_format_catalog_table_contains_indices():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    table = format_catalog_table(catalog)
    assert "1." in table
    assert "Save" in table
    assert "mysz:" in table


def test_prompt_to_imgl_uri_click_polish():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    resolved = prompt_to_imgl_uri(
        "kliknij Save",
        image="/tmp/dialog.png",
        catalog=catalog,
    )
    assert resolved is not None
    assert resolved.match_reason == "catalog:text"
    assert "action=click" in resolved.uri
    assert resolved.action_payload is not None
    assert resolved.action_payload["action"] == "click"


def test_prompt_to_imgl_uri_type_polish():
    resolved = prompt_to_imgl_uri(
        'wpisz hello w Username',
        image="/tmp/dialog.png",
    )
    assert resolved is not None
    assert "action=type" in resolved.uri
    assert "value=hello" in resolved.uri


def test_prompt_to_imgl_uri_number():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    resolved = prompt_to_imgl_uri("2", image="/tmp/dialog.png", catalog=catalog)
    assert resolved is not None
    assert resolved.option_index == 2


def test_resolve_imgl_uri_click():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    session = InteractSession(
        image_path="/tmp/dialog.png",
        vql_file="layout.vql.json",
        lang="eng",
        scene=scene,
        catalog=catalog,
    )
    uri = uri_for_imgl_click(image="/tmp/dialog.png", file="layout.vql.json", text="Save")
    result = resolve_imgl_uri(uri, session)
    assert result["ok"] is True
    assert result["action"] == "click"
    assert result["text"] == "Save"


def test_resolve_imgl_uri_list():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    session = InteractSession(
        image_path="/tmp/dialog.png",
        vql_file="layout.vql.json",
        lang="eng",
        scene=scene,
        catalog=catalog,
    )
    uri = uri_for_imgl_list(image="/tmp/dialog.png", file="layout.vql.json")
    result = resolve_imgl_uri(uri, session)
    assert result["ok"] is True
    assert result["action"] == "list"
    assert result["count"] == 3


def test_resolve_imgl_uri_type():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    session = InteractSession(
        image_path="/tmp/dialog.png",
        vql_file="layout.vql.json",
        lang="eng",
        scene=scene,
        catalog=catalog,
    )
    uri = uri_for_imgl_type(
        image="/tmp/dialog.png",
        file="layout.vql.json",
        value="alice",
        label="Username",
    )
    result = resolve_imgl_uri(uri, session)
    assert result["ok"] is True
    assert result["action"] == "type"
    assert result["text"] == "alice"


def test_catalog_input_number_is_click():
    scene = _dialog_scene()
    catalog = build_interactive_catalog(scene, image_path="/tmp/dialog.png")
    input_opt = next(opt for opt in catalog if opt.category == "input")
    resolved = prompt_to_imgl_uri(
        str(input_opt.index),
        image="/tmp/dialog.png",
        catalog=catalog,
    )
    assert resolved is not None
    assert "action=click" in resolved.uri
    assert resolved.action_payload is not None
    assert resolved.action_payload["action"] == "click"


def test_interactive_shell_quit(monkeypatch):
    scene = _dialog_scene()

    def fake_analyze(*_args, **_kwargs):
        return scene

    monkeypatch.setattr("imgl.interact.load_or_analyze", fake_analyze)
    monkeypatch.setattr("imgl.interact.write_vql_program", lambda *_a, **_k: None)

    stdin = io.StringIO("quit\n")
    stdout = io.StringIO()
    stderr = io.StringIO()
    code = run_interactive_shell(
        "/tmp/dialog.png",
        input_stream=stdin,
        output_stream=stdout,
    )
    assert code == 0
    assert "Koniec" in stdout.getvalue()
