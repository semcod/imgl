"""Text-based UI actions on analyzed scenes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from imgl.geometry import bbox_distance
from imgl.types import Element, Scene, Window


@dataclass
class ActionTarget:
    """A resolved UI element that can be clicked or typed into."""

    element: Element
    window: Window | None = None

    def center(self) -> tuple[int, int]:
        bbox = self.element.bbox
        return (bbox.x + bbox.w // 2, bbox.y + bbox.h // 2)

    def click_coords(self) -> tuple[int, int]:
        """Return pixel coordinates for a click at element center."""
        return self.center()

    def to_click_action(self) -> dict[str, Any]:
        x, y = self.click_coords()
        return {
            "action": "click",
            "x": x,
            "y": y,
            "element_id": self.element.id,
            "element_type": self.element.type,
            "text": self.element.text,
            "window_id": self.window.id if self.window else None,
            "bbox": self.element.bbox.to_dict(),
        }


@dataclass
class TypeAction:
    """Type text into an input field."""

    target: ActionTarget
    value: str
    label: str | None = None

    def coords(self) -> tuple[int, int]:
        return self.target.click_coords()

    def to_dict(self) -> dict[str, Any]:
        x, y = self.coords()
        return {
            "action": "type",
            "x": x,
            "y": y,
            "text": self.value,
            "element_id": self.target.element.id,
            "element_type": self.target.element.type,
            "label": self.label,
            "window_id": self.target.window.id if self.target.window else None,
            "bbox": self.target.element.bbox.to_dict(),
        }


@dataclass
class SceneActions:
    """Find and interact with elements in a Scene."""

    scene: Scene

    def find(
        self,
        element_type: str | None = None,
        *,
        text: str | None = None,
        label: str | None = None,
        window: str | None = None,
        contains: bool = True,
    ) -> list[ActionTarget]:
        """Find elements matching type, text, label, or window."""
        targets: list[ActionTarget] = []

        for win, element in _iter_elements(self.scene, window=window):
            if element_type and element.type != element_type:
                continue
            if text is not None and not _text_matches(element.text, text, contains=contains):
                continue
            if label is not None:
                if element.type == "input":
                    input_label = element.metadata.get("label") or ""
                    if not _text_matches(str(input_label), label, contains=contains):
                        continue
                elif element.type == "label":
                    if not _text_matches(element.text, label, contains=contains):
                        continue
                else:
                    continue
            targets.append(ActionTarget(element=element, window=win))

        if label is not None and element_type in {None, "input"}:
            targets.extend(self._find_labeled_inputs(label, window, targets, contains))

        return targets

    def _find_labeled_inputs(
        self,
        label: str,
        window: str | None,
        existing: list[ActionTarget],
        contains: bool,
    ) -> list[ActionTarget]:
        from imgl.catalog import _infer_input_label

        existing_ids = {t.element.id for t in existing}
        extra: list[ActionTarget] = []
        for win, element in _iter_elements(self.scene, window=window):
            if element.type != "input" or element.id in existing_ids:
                continue
            matched_label = _find_label_for_input(self.scene, element, win)
            if matched_label and _text_matches(matched_label.text, label, contains=contains):
                extra.append(ActionTarget(element=element, window=win))
                continue
            inferred = _infer_input_label(element, win)
            if _text_matches(inferred, label, contains=contains):
                extra.append(ActionTarget(element=element, window=win))
        return extra

    def find_one(
        self,
        element_type: str | None = None,
        *,
        text: str | None = None,
        label: str | None = None,
        window: str | None = None,
        contains: bool = True,
    ) -> ActionTarget | None:
        matches = self.find(
            element_type,
            text=text,
            label=label,
            window=window,
            contains=contains,
        )
        return matches[0] if matches else None

    def click(
        self,
        element_type: str | None = None,
        *,
        text: str | None = None,
        label: str | None = None,
        window: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a click action for the first matching element."""
        target = self.find_one(element_type, text=text, label=label, window=window)
        if target is None:
            raise ElementNotFoundError(
                _format_query(element_type, text=text, label=label, window=window)
            )
        return target.to_click_action()

    def type_into(
        self,
        value: str,
        *,
        label: str | None = None,
        text: str | None = None,
        window: str | None = None,
    ) -> dict[str, Any]:
        """Resolve a type action for an input field."""
        target = self.find_one("input", label=label, text=text, window=window)
        if target is None and text is not None:
            target = self.find_one("input", text=text, window=window)
        if target is None:
            raise ElementNotFoundError(
                _format_query("input", text=text, label=label, window=window)
            )
        resolved_label = label or target.element.metadata.get("label")
        return TypeAction(target=target, value=value, label=resolved_label).to_dict()

    def list_actions(self) -> list[dict[str, Any]]:
        """List available click/type actions for interactive elements."""
        actions: list[dict[str, Any]] = []
        for _, element in _iter_elements(self.scene):
            if element.type in {"button", "icon_button"}:
                actions.append(ActionTarget(element=element).to_click_action())
            elif element.type == "input":
                actions.append(
                    TypeAction(
                        target=ActionTarget(element=element),
                        value=element.text or "",
                        label=element.metadata.get("label"),
                    ).to_dict()
                )
        return actions


class ElementNotFoundError(LookupError):
    """Raised when no element matches the query."""


def actions(scene: Scene) -> SceneActions:
    """Create a SceneActions helper for a scene."""
    return SceneActions(scene)


def _format_query(
    element_type: str | None,
    *,
    text: str | None,
    label: str | None,
    window: str | None,
) -> str:
    parts = []
    if element_type:
        parts.append(f"type={element_type}")
    if text:
        parts.append(f"text={text!r}")
    if label:
        parts.append(f"label={label!r}")
    if window:
        parts.append(f"window={window!r}")
    return "element not found: " + ", ".join(parts)


def _text_matches(value: str | None, query: str, *, contains: bool) -> bool:
    if value is None:
        return False
    left = value.casefold()
    right = query.casefold()
    return right in left if contains else left == right


def _iter_elements(
    scene: Scene,
    *,
    window: str | None = None,
) -> Iterable[tuple[Window | None, Element]]:
    if window is not None:
        from imgl.window_scope import get_discovered_window

        resolved = get_discovered_window(scene, window)
        if resolved is not None:
            window = resolved.id
    for win in scene.windows:
        if window is not None and not _window_matches(win, window):
            continue
        for element in win.elements:
            yield win, element
    if window is None:
        for element in scene.orphan_elements:
            yield None, element


def _window_matches(window: Window, query: str) -> bool:
    query_cf = query.casefold()
    if window.id.casefold() == query_cf:
        return True
    if window.title and query_cf in window.title.casefold():
        return True
    return False


def _find_label_for_input(
    scene: Scene,
    input_element: Element,
    window: Window | None,
) -> Element | None:
    candidates: list[Element] = []
    for win, element in _iter_elements(scene, window=window.id if window else None):
        if element.type != "label":
            continue
        if element.metadata.get("for_input") == input_element.id:
            return element
        candidates.append(element)

    if not candidates:
        return None
    return min(candidates, key=lambda label: bbox_distance(label.bbox, input_element.bbox))
