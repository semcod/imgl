from __future__ import annotations

from imgl.export.actuation_layers import (
    bbox_area,
    imgl_result_to_actuation_layers,
    scene_to_actuation_layers,
)


def test_scene_to_actuation_layers_flattens_window_elements_and_ocr() -> None:
    scene = {
        "windows": [
            {
                "id": "window_0",
                "bbox": {"x": 0, "y": 0, "w": 100, "h": 50},
                "elements": [
                    {
                        "id": "window_0-input-1",
                        "type": "input",
                        "text": "editor",
                        "bbox": {"x": 10, "y": 20, "w": 80, "h": 10},
                        "confidence": 0.9,
                    }
                ],
            }
        ],
        "ocr_boxes": [{"text": "Ask", "bbox": {"x": 5, "y": 5, "w": 20, "h": 10}, "confidence": 90.0}],
    }
    layers = scene_to_actuation_layers(scene)
    assert len(layers) >= 3
    editor = next(item for item in layers if item.get("text") == "editor")
    assert editor["click_center"] == {"x": 50, "y": 25}
    ask = next(item for item in layers if item.get("text") == "Ask")
    assert ask["kind"] == "ocr"


def test_bbox_area_supports_w_h() -> None:
    assert bbox_area({"x": 0, "y": 0, "w": 2040, "h": 1272}) == 2040 * 1272


def test_imgl_result_to_actuation_layers_requires_ok() -> None:
    assert imgl_result_to_actuation_layers({"ok": False}) == []
    assert imgl_result_to_actuation_layers({"ok": True, "scene": {"windows": []}}) == []
