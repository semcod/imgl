"""JSON serialization for Scene models."""

from __future__ import annotations

import json
from typing import Any

from imgl.types import Scene


def scene_to_json(scene: Scene, *, indent: int = 2) -> str:
    """Serialize a Scene to a JSON string."""
    return json.dumps(scene.to_dict(), indent=indent, ensure_ascii=False)


def scene_from_json(payload: str | dict[str, Any]) -> Scene:
    """Deserialize a Scene from JSON."""
    if isinstance(payload, str):
        data = json.loads(payload)
    else:
        data = payload
    return Scene.from_dict(data)
