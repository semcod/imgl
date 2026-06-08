"""OCR backends for text extraction."""

from .base import OcrBackend
from .tesseract import TesseractOcr

__all__ = ["OcrBackend", "TesseractOcr", "get_ocr_backend"]


def get_ocr_backend(name: str = "tesseract") -> OcrBackend:
    if name == "tesseract":
        return TesseractOcr()
    raise ValueError(f"Unknown OCR backend: {name}")
