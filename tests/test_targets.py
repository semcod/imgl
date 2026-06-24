from __future__ import annotations

from imgl.targets import resolve_chat_target, resolve_editor_target


def test_resolve_chat_prefers_panel_over_send_chat_ocr_label() -> None:
    layers = [
        {
            "kind": "input",
            "id": "window_0-input-50",
            "label": "send_chat",
            "bbox": {"x": 964, "y": 507, "w": 77, "h": 17},
            "click_center": {"x": 1002, "y": 515},
        },
        {
            "kind": "panel",
            "id": "panel_3",
            "bbox": {"x": 700, "y": 300, "w": 320, "h": 280},
            "click_center": {"x": 854, "y": 440},
            "location": "center",
        },
    ]
    target = resolve_chat_target(layers, source="test.vql.json")
    assert target["id"] == "panel_3"
    assert target["click_center"] == {"x": 854, "y": 440}


def test_resolve_editor_prefers_window_0() -> None:
    layers = [
        {
            "kind": "window",
            "id": "window_0",
            "bbox": {"x": 0, "y": 0, "w": 2040, "h": 1272},
            "click_center": {"x": 1020, "y": 636},
        }
    ]
    target = resolve_editor_target(layers, source="test.vql.json")
    assert target["id"] == "window_0"
    assert target["click_center"] == {"x": 1020, "y": 636}


def test_resolve_chat_picks_bottom_right_input() -> None:
    layers = [
        {
            "kind": "input",
            "id": "window_0-input-24",
            "bbox": {"x": 968, "y": 1079, "w": 192, "h": 26},
            "click_center": {"x": 1064, "y": 1092},
        },
        {
            "kind": "input",
            "id": "window_0-input-25",
            "bbox": {"x": 1006, "y": 247, "w": 116, "h": 34},
            "click_center": {"x": 1064, "y": 264},
        },
    ]
    target = resolve_chat_target(layers, source="test.vql.json")
    assert target["id"] == "window_0-input-24"
