"""Core data types for screenshot layout analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BBox:
    x: int
    y: int
    w: int
    h: int

    def as_xyxy(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.w, self.y + self.h)

    def contains(self, other: BBox) -> bool:
        ox0, oy0, ox1, oy1 = other.as_xyxy()
        x0, y0, x1, y1 = self.as_xyxy()
        return x0 <= ox0 and y0 <= oy0 and x1 >= ox1 and y1 >= oy1

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    @classmethod
    def from_xyxy(cls, x0: int, y0: int, x1: int, y1: int) -> BBox:
        return cls(x=x0, y=y0, w=max(0, x1 - x0), h=max(0, y1 - y0))


@dataclass
class OcrBox:
    text: str
    bbox: BBox
    confidence: float
    level: str = "word"

    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "confidence": round(self.confidence, 3),
            "level": self.level,
        }


@dataclass
class Element:
    id: str
    type: str
    text: str | None
    bbox: BBox
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list[Element] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "confidence": round(self.confidence, 3),
            "metadata": self.metadata,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class Window:
    id: str
    bbox: BBox
    title: str | None
    z: int
    elements: list[Element] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "bbox": self.bbox.to_dict(),
            "title": self.title,
            "z": self.z,
            "elements": [element.to_dict() for element in self.elements],
        }


@dataclass
class Scene:
    width: int
    height: int
    source_image: str | None = None
    windows: list[Window] = field(default_factory=list)
    orphan_elements: list[Element] = field(default_factory=list)
    ocr_boxes: list[OcrBox] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": "1.0",
            "scene": {
                "width": self.width,
                "height": self.height,
                "source_image": self.source_image,
            },
            "windows": [window.to_dict() for window in self.windows],
            "orphan_elements": [element.to_dict() for element in self.orphan_elements],
            "ocr_boxes": [box.to_dict() for box in self.ocr_boxes],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scene:
        scene_data = data.get("scene", {})

        def bbox_from_dict(raw: dict[str, int]) -> BBox:
            return BBox(**raw)

        def element_from_dict(raw: dict[str, Any]) -> Element:
            return Element(
                id=raw["id"],
                type=raw["type"],
                text=raw.get("text"),
                bbox=bbox_from_dict(raw["bbox"]),
                confidence=raw.get("confidence", 0.5),
                metadata=raw.get("metadata", {}),
                children=[element_from_dict(child) for child in raw.get("children", [])],
            )

        windows = [
            Window(
                id=raw["id"],
                bbox=bbox_from_dict(raw["bbox"]),
                title=raw.get("title"),
                z=raw.get("z", 0),
                elements=[element_from_dict(element) for element in raw.get("elements", [])],
            )
            for raw in data.get("windows", [])
        ]

        orphan_elements = [
            element_from_dict(raw) for raw in data.get("orphan_elements", [])
        ]

        ocr_boxes = [
            OcrBox(
                text=raw["text"],
                bbox=bbox_from_dict(raw["bbox"]),
                confidence=raw.get("confidence", 0.0),
                level=raw.get("level", "word"),
            )
            for raw in data.get("ocr_boxes", [])
        ]

        return cls(
            width=scene_data.get("width", 0),
            height=scene_data.get("height", 0),
            source_image=scene_data.get("source_image"),
            windows=windows,
            orphan_elements=orphan_elements,
            ocr_boxes=ocr_boxes,
            metadata=data.get("metadata", {}),
        )


def dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """Convert a dataclass instance to a plain dict."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return asdict(obj)
