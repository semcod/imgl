"""Image preprocessing for layout analysis."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image

from imgl.paths import resolve_image_path

ImageSource = Union[str, Path, bytes]

SUPPORTED_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp", ".tiff", ".tif"}


@dataclass
class PreprocessedImage:
    image: Image.Image
    width: int
    height: int
    scale: float
    source_path: str | None


def load_image(source: ImageSource) -> tuple[Image.Image, str | None]:
    """Load an image from path or raw bytes."""
    if isinstance(source, bytes):
        image = Image.open(BytesIO(source))
        return image.convert("RGB"), None

    path = resolve_image_path(source)
    image = Image.open(path)
    return image.convert("RGB"), str(path)


def preprocess(
    source: ImageSource,
    *,
    max_dim: int = 4000,
) -> PreprocessedImage:
    """Load and optionally downscale an image for analysis."""
    image, source_path = load_image(source)
    width, height = image.size
    scale = 1.0

    longest = max(width, height)
    if max_dim > 0 and longest > max_dim:
        scale = max_dim / longest
        new_width = max(1, int(width * scale))
        new_height = max(1, int(height * scale))
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        width, height = image.size

    return PreprocessedImage(
        image=image,
        width=width,
        height=height,
        scale=scale,
        source_path=source_path,
    )
