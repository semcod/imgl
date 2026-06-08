"""Configuration for imgl analysis pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImglConfig:
    lang: str = "eng+pol"
    max_dim: int = 4000
    ocr_backend: str = "tesseract"
    min_ocr_confidence: float = 30.0
    use_img2vql: bool = True
    detect_inputs: bool = True
    label_proximity_px: float = 40.0
    check_content: bool = True
    skip_blank: bool = False
    diagnose_locale: str = "pl"
