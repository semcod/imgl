"""Tesseract OCR backend."""

from __future__ import annotations

from PIL import Image

from imgl.ocr.lang import ocr_lang_attempts
from imgl.types import BBox, OcrBox

try:
    import pytesseract
except ImportError:  # pragma: no cover - optional at import time
    pytesseract = None  # type: ignore[assignment]


class TesseractOcr:
    """Extract word-level bounding boxes using pytesseract."""

    def run(
        self,
        image: Image.Image,
        *,
        lang: str = "eng",
        min_confidence: float = 30.0,
    ) -> list[OcrBox]:
        if pytesseract is None:
            raise ImportError(
                "pytesseract is required for OCR. Install with: pip install 'imgl[ocr]' "
                "(plus the system tesseract binary, e.g. apt install tesseract-ocr)"
            )

        data = None
        last_error: Exception | None = None
        for attempt_lang in ocr_lang_attempts(lang):
            try:
                data = pytesseract.image_to_data(
                    image,
                    lang=attempt_lang,
                    output_type=pytesseract.Output.DICT,
                )
                break
            except pytesseract.TesseractError as exc:
                last_error = exc
        if data is None:
            if last_error is not None:
                raise last_error
            raise RuntimeError(f"Tesseract OCR failed for lang={lang!r}")

        boxes: list[OcrBox] = []
        count = len(data["text"])

        for index in range(count):
            text = (data["text"][index] or "").strip()
            if not text:
                continue

            try:
                confidence = float(data["conf"][index])
            except (ValueError, TypeError):
                confidence = 0.0

            if confidence < min_confidence:
                continue

            left = int(data["left"][index])
            top = int(data["top"][index])
            width = int(data["width"][index])
            height = int(data["height"][index])
            if width <= 0 or height <= 0:
                continue

            level_num = int(data["level"][index])
            level = _level_name(level_num)

            boxes.append(
                OcrBox(
                    text=text,
                    bbox=BBox(x=left, y=top, w=width, h=height),
                    confidence=confidence,
                    level=level,
                )
            )

        return boxes


def _level_name(level: int) -> str:
    mapping = {
        1: "page",
        2: "block",
        3: "paragraph",
        4: "line",
        5: "word",
    }
    return mapping.get(level, "word")
