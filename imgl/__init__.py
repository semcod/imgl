"""
imgl - Image to Layout

Convert screenshots into semantic UI models (JSON/HTML/SVG) with OCR text
and element bounding boxes.
"""

__version__ = "0.7.1"
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
)
from imgl.pipeline import analyze
from imgl.types import BBox, Element, OcrBox, Scene, Window

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
]
