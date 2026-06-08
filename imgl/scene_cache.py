"""Cache analyzed Scene JSON to avoid repeated OCR on large screenshots."""

from __future__ import annotations

import json
from pathlib import Path

from imgl.config import ImglConfig
from imgl.export import scene_from_json, scene_to_json
from imgl.pipeline import analyze
from imgl.types import Scene


def scene_cache_path(vql_file: str | Path) -> Path:
    path = Path(vql_file)
    if path.suffix == ".json":
        return path.with_name(path.stem + ".imgl.json")
    return path.with_suffix(path.suffix + ".imgl.json")


def load_cached_scene(image_path: str | Path, vql_file: str | Path) -> Scene | None:
    """Return cached scene when image path matches."""
    cache = scene_cache_path(vql_file)
    if not cache.is_file():
        return None
    try:
        scene = scene_from_json(cache.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        return None
    expected = str(Path(image_path).resolve())
    if scene.source_image and str(Path(scene.source_image).resolve()) == expected:
        return scene
    return None


def save_scene_cache(scene: Scene, vql_file: str | Path) -> Path:
    cache = scene_cache_path(vql_file)
    cache.write_text(scene_to_json(scene), encoding="utf-8")
    return cache


def load_or_analyze(
    image_path: str | Path,
    *,
    vql_file: str | Path,
    lang: str | None = None,
    config: ImglConfig | None = None,
    refresh: bool = False,
) -> Scene:
    """Load scene from cache or run analyze() and persist cache."""
    image = str(Path(image_path).resolve())
    if not refresh:
        cached = load_cached_scene(image, vql_file)
        if cached is not None:
            return cached

    cfg = config or ImglConfig()
    if lang is not None:
        cfg.lang = lang
    scene = analyze(image, config=cfg)
    save_scene_cache(scene, vql_file)
    return scene

