"""OCR backend protocol."""

from __future__ import annotations

from typing import Protocol

from PIL import Image

from imgl.types import OcrBox


class OcrBackend(Protocol):
    def run(self, image: Image.Image, *, lang: str = "eng") -> list[OcrBox]:
        """Extract text boxes from an image."""
