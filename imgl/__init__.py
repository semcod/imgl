"""
imgl - Image to Layout

Convert screenshots into semantic UI models (JSON/HTML/SVG) with OCR text
and element bounding boxes.
"""

__version__ = "0.7.17"
__author__ = "Tom Sapletta"
__email__ = "tom@sapletta.com"

from imgl.actions import ActionTarget, ElementNotFoundError, SceneActions, TypeAction, actions
from imgl.config import ImglConfig
from imgl.diagnose import BlankImageError, diagnose_content, worth_analyzing
from imgl.export import (
    scene_from_json,
    scene_to_html,
    scene_to_json,
    scene_to_svg,
    scene_to_vql,
    scene_to_vql_json,
    write_vql_program,
    scene_to_actuation_layers,
    imgl_result_to_actuation_layers,
    bbox_area,
    bbox_center,
)
from imgl.pipeline import analyze
from imgl.targets import (
    normalize_actuation_element,
    resolve_actuation_target,
    resolve_chat_target,
    resolve_editor_target,
)
from imgl.types import BBox, Element, OcrBox, Scene, Window
from imgl.vdisplay_context import enrich_scene_from_vdisplay, from_vdisplay_context
from imgl.vision_ops import (
    MatchOverlayItem,
    TemplateMatchResult,
    diff_png_bytes,
    match_template_png,
    render_match_overlay_png,
    template_available,
)

__all__ = [
    "__version__",
    "analyze",
    "scene_to_json",
    "scene_from_json",
    "scene_to_html",
    "scene_to_svg",
    "scene_to_vql",
    "scene_to_vql_json",
    "write_vql_program",
    "scene_to_actuation_layers",
    "imgl_result_to_actuation_layers",
    "bbox_area",
    "bbox_center",
    "normalize_actuation_element",
    "resolve_actuation_target",
    "resolve_chat_target",
    "resolve_editor_target",
    "actions",
    "SceneActions",
    "ActionTarget",
    "TypeAction",
    "ElementNotFoundError",
    "BlankImageError",
    "diagnose_content",
    "worth_analyzing",
    "ImglConfig",
    "BBox",
    "OcrBox",
    "Element",
    "Window",
    "Scene",
    "from_vdisplay_context",
    "enrich_scene_from_vdisplay",
    "TemplateMatchResult",
    "MatchOverlayItem",
    "match_template_png",
    "render_match_overlay_png",
    "template_available",
    "diff_png_bytes",
]
