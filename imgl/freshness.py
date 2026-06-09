"""Screenshot freshness, OCR cache invalidation, capture sidecar."""

from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from pathlib import Path

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 64


def is_valid_png(image: str | Path, *, min_bytes: int = _MIN_PNG_BYTES) -> bool:
    """True when file exists and looks like a non-trivial PNG."""
    path = Path(image).expanduser()
    if not path.is_file():
        return False
    size = path.stat().st_size
    if size < min_bytes:
        return False
    with path.open("rb") as handle:
        return handle.read(8) == _PNG_MAGIC


def max_image_age_seconds() -> int:
    for key in ("IMGL_MAX_AGE_SEC", "KORU_IMGL_MAX_AGE_SEC"):
        raw = os.environ.get(key, "").strip()
        if raw:
            try:
                return max(1, int(raw))
            except ValueError:
                pass
    return 60


def capture_sidecar_path(image: Path) -> Path:
    return image.with_suffix(".captured_at")


def vql_cache_paths(image: Path) -> list[Path]:
    return [
        image.with_suffix(".vql.imgl.json"),
        image.with_suffix(".vql.json"),
    ]


def clear_vql_cache(image: Path) -> list[str]:
    removed: list[str] = []
    for cache in vql_cache_paths(image):
        if cache.is_file():
            cache.unlink()
            removed.append(str(cache))
    return removed


def sync_vql_cache_with_image(image: Path) -> list[str]:
    """Invalidate OCR cache when PNG is newer than sidecar files."""
    if not image.is_file():
        return []
    png_mtime = image.stat().st_mtime
    stale = any(
        cache.is_file() and cache.stat().st_mtime < png_mtime for cache in vql_cache_paths(image)
    )
    if stale:
        return clear_vql_cache(image)
    return []


def mark_capture_fresh(image: Path) -> Path:
    """Record capture time (sidecar) and bump PNG mtime."""
    image = image.expanduser()
    if not is_valid_png(image):
        raise ValueError(f"capture is not a valid PNG: {image}")
    sidecar = capture_sidecar_path(image)
    now = time.time()
    sidecar.write_text(f"{now:.6f}", encoding="utf-8")
    os.utime(image, (now, now))
    return sidecar


def image_freshness(image_path: str | Path) -> dict:
    path = Path(image_path).expanduser()
    max_age = max_image_age_seconds()
    if not path.is_file():
        return {
            "ok": False,
            "path": str(path),
            "exists": False,
            "age_seconds": None,
            "max_age_seconds": max_age,
            "is_fresh": False,
            "error": f"image not found: {path}",
        }
    mtime = path.stat().st_mtime
    sidecar = capture_sidecar_path(path)
    captured_at = mtime
    capture_source = "png_mtime"
    if sidecar.is_file():
        try:
            captured_at = max(mtime, float(sidecar.read_text().strip()))
            capture_source = "sidecar"
        except ValueError:
            captured_at = mtime
    age = max(0.0, time.time() - captured_at)
    return {
        "ok": True,
        "path": str(path),
        "exists": True,
        "mtime": mtime,
        "captured_at": captured_at,
        "capture_source": capture_source,
        "sidecar": str(sidecar) if sidecar.is_file() else None,
        "mtime_iso": datetime.fromtimestamp(captured_at, tz=timezone.utc).astimezone().isoformat(),
        "age_seconds": round(age, 1),
        "max_age_seconds": max_age,
        "is_fresh": age <= max_age,
        "error": None,
    }


def verify_capture_updated(image: str | Path, before_mtime: float) -> None:
    path = Path(image).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"capture output missing: {path}")
    after = path.stat().st_mtime
    if after <= before_mtime:
        raise RuntimeError(
            f"capture did not update {path} — select area in GNOME portal or retry "
            "`imgl capture --interactive -o <path>`"
        )
    if not is_valid_png(path):
        size = path.stat().st_size
        raise RuntimeError(
            f"capture produced invalid PNG ({size} bytes): {path} — "
            "use `imgl capture --interactive -o screen.png --verify` (portal GNOME), not vdisplay mirror on Wayland"
        )
    mark_capture_fresh(path)


__all__ = [
    "capture_sidecar_path",
    "clear_vql_cache",
    "image_freshness",
    "is_valid_png",
    "mark_capture_fresh",
    "max_image_age_seconds",
    "sync_vql_cache_with_image",
    "verify_capture_updated",
    "vql_cache_paths",
]
