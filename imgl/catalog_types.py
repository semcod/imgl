"""Shared types for interactive catalog builders."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InteractiveOption:
    """One selectable UI target with mouse/keyboard affordances."""

    index: int
    category: str
    element_id: str
    element_type: str
    label: str
    text: str | None
    window_id: str | None
    window_title: str | None
    position: tuple[int, int]
    bbox: dict[str, int]
    mouse_actions: list[str] = field(default_factory=list)
    keyboard_actions: list[str] = field(default_factory=list)
    primary_action: str = "click"
    action_uri: str = ""
    action_payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "category": self.category,
            "element_id": self.element_id,
            "element_type": self.element_type,
            "label": self.label,
            "text": self.text,
            "window_id": self.window_id,
            "window_title": self.window_title,
            "position": {"x": self.position[0], "y": self.position[1]},
            "bbox": self.bbox,
            "mouse_actions": self.mouse_actions,
            "keyboard_actions": self.keyboard_actions,
            "primary_action": self.primary_action,
            "action_uri": self.action_uri,
            "action_payload": self.action_payload,
        }
