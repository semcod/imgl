"""Coordinate transforms between analysis scale and screen pixels."""

from __future__ import annotations

from imgl.types import BBox, Element, OcrBox, Scene, Window


def scale_scene_to_screen(scene: Scene, *, scale: float) -> Scene:
    """Map analyzed coordinates back to original screenshot pixel space."""
    if scale >= 0.999:
        return scene

    inv = 1.0 / scale
    orig_w = max(1, int(round(scene.width * inv)))
    orig_h = max(1, int(round(scene.height * inv)))

    def up_bbox(bbox: BBox) -> BBox:
        return BBox(
            x=int(round(bbox.x * inv)),
            y=int(round(bbox.y * inv)),
            w=max(1, int(round(bbox.w * inv))),
            h=max(1, int(round(bbox.h * inv))),
        )

    def up_element(element: Element) -> Element:
        return Element(
            id=element.id,
            type=element.type,
            text=element.text,
            bbox=up_bbox(element.bbox),
            confidence=element.confidence,
            metadata=dict(element.metadata),
            children=[up_element(child) for child in element.children],
        )

    windows = [
        Window(
            id=window.id,
            bbox=up_bbox(window.bbox),
            title=window.title,
            z=window.z,
            elements=[up_element(element) for element in window.elements],
        )
        for window in scene.windows
    ]
    orphans = [up_element(element) for element in scene.orphan_elements]
    ocr_boxes = [
        OcrBox(
            text=box.text,
            bbox=up_bbox(box.bbox),
            confidence=box.confidence,
            level=box.level,
        )
        for box in scene.ocr_boxes
    ]

    metadata = dict(scene.metadata)
    metadata["analysis_scale"] = scale
    metadata["screen_width"] = orig_w
    metadata["screen_height"] = orig_h

    return Scene(
        width=orig_w,
        height=orig_h,
        source_image=scene.source_image,
        windows=windows,
        orphan_elements=orphans,
        ocr_boxes=ocr_boxes,
        metadata=metadata,
    )
