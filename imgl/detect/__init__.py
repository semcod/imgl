"""UI element detection backends."""

from .img2vql_bridge import detect_ui_merged, detect_with_img2vql
from .local import DetectedUI, detect_ui_elements

__all__ = [
    "DetectedUI",
    "detect_ui_elements",
    "detect_ui_merged",
    "detect_with_img2vql",
]
