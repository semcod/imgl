"""Content quality checks via img2nl (blank / meaningful screen detection)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

BLANK_SCENE_CLASSES = frozenset({"empty_dark_screen", "unchanged_screen"})
LOW_VALUE_SCENE_CLASSES = frozenset({"flat_monochrome"})


class BlankImageError(ValueError):
    """Raised when a screenshot has no meaningful UI content."""


def img2nl_available() -> bool:
    try:
        import img2nl  # noqa: F401

        return True
    except ImportError:
        return False


def diagnose_content(
    image_path: str | Path,
    *,
    locale: str = "pl",
    reference_fingerprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Analyze whether an image has meaningful UI content (img2nl heuristics).

    Falls back to vql image_stats or a minimal PIL check when img2nl is absent.
    """
    path = Path(image_path).expanduser()
    if not path.is_file():
        return {"ok": False, "path": str(path), "error": f"image not found: {path}"}

    if img2nl_available():
        return _diagnose_with_img2nl(
            path,
            locale=locale,
            reference_fingerprint=reference_fingerprint,
        )

    fallback = _diagnose_fallback(path)
    fallback["source"] = "fallback"
    return fallback


def worth_analyzing(diag: dict[str, Any]) -> bool:
    """True when the image likely contains analyzable UI (not blank/empty)."""
    if not diag.get("ok"):
        return True

    if diag.get("is_blank"):
        return False

    scene_class = _scene_class(diag)
    if scene_class in BLANK_SCENE_CLASSES:
        return False

    if scene_class in LOW_VALUE_SCENE_CLASSES:
        return _has_ui_signals(diag)

    recommendation = diag.get("recommendation", "")
    if recommendation in {"skip_blank_capture", "skip_unchanged_screen"}:
        return False

    return True


def content_summary(diag: dict[str, Any], *, locale: str = "pl") -> str:
    """Short human-readable summary (img2nl text when available)."""
    if diag.get("text"):
        return str(diag["text"])
    if not diag.get("ok"):
        return str(diag.get("error", "diagnose failed"))
    scene_class = _scene_class(diag)
    if scene_class == "empty_dark_screen":
        return "Pusty lub ciemny ekran — brak treści do analizy."
    if scene_class == "unchanged_screen":
        return "Ekran bez zmian względem poprzedniego zrzutu."
    if scene_class == "flat_monochrome":
        return "Płaska powierzchnia jednokolorowa — mało treści UI."
    return f"Scena: {scene_class}"


def _diagnose_with_img2nl(
    path: Path,
    *,
    locale: str,
    reference_fingerprint: dict[str, Any] | None,
) -> dict[str, Any]:
    from img2nl import analyze_image

    result = analyze_image(
        path,
        skip_thumbnail=True,
        locale=locale,
        reference_fingerprint=reference_fingerprint,
    )
    if not result.ok:
        return {"ok": False, "path": str(path), "error": result.error, "source": "img2nl"}

    payload = {
        "ok": True,
        "path": result.path,
        "width": result.width,
        "height": result.height,
        "text": result.text,
        "features": result.features,
        "llm_hint": result.llm_hint,
        "locale": result.locale,
        "source": "img2nl",
    }
    payload["scene_class"] = _scene_class(payload)
    payload["worth_analyzing"] = worth_analyzing(payload)
    payload["recommendation"] = _recommendation(payload)
    payload["is_blank"] = not payload["worth_analyzing"]
    return payload


def _diagnose_fallback(path: Path) -> dict[str, Any]:
    try:
        from vql.adopt.window import image_stats

        stats = image_stats(path)
        if not stats.get("ok"):
            return stats
        is_blank = bool(stats.get("is_blank"))
        unique = int(stats.get("unique_colors_sampled", 0))
        payload = {
            "ok": True,
            "path": str(path),
            "width": stats.get("width", 0),
            "height": stats.get("height", 0),
            "features": {
                "colors": {
                    "unique_colors_sampled": unique,
                    "is_mostly_dark": int(stats.get("brightness_avg", 128)) < 16,
                    "is_monochrome": unique <= 2,
                },
                "scene": {
                    "scene_class": "empty_dark_screen" if is_blank else "general",
                    "labels": ["fallback_stats"],
                },
            },
            "llm_hint": {
                "send_to_llm": not is_blank,
                "recommendation": "skip" if is_blank else "send",
            },
            "text": (
                "Pusty zrzut (all black)"
                if is_blank
                else (
                    f"Obraz {stats.get('width')}×{stats.get('height')} px, "
                    f"~{unique} kolorów (vql stats)."
                )
            ),
            "scene_class": "empty_dark_screen" if is_blank else "general",
            "worth_analyzing": not is_blank,
            "recommendation": "skip_blank_capture" if is_blank else "proceed_with_layout",
            "is_blank": is_blank,
        }
        return payload
    except ImportError:
        pass

    return _diagnose_pil_fallback(path)


def _diagnose_pil_fallback(path: Path) -> dict[str, Any]:
    from PIL import Image

    image = Image.open(path).convert("RGB")
    w, h = image.size
    small = image.resize((32, 32))
    pixels = list(small.get_flattened_data())
    unique = len(set(pixels))
    is_dark = all(max(px) < 12 for px in pixels)
    is_blank = unique <= 1 and is_dark

    return {
        "ok": True,
        "path": str(path),
        "width": w,
        "height": h,
        "features": {
            "colors": {"unique_colors_sampled": unique, "is_monochrome": unique <= 2},
            "scene": {"scene_class": "empty_dark_screen" if is_blank else "general"},
        },
        "text": "Pusty zrzut" if is_blank else "",
        "scene_class": "empty_dark_screen" if is_blank else "general",
        "worth_analyzing": not is_blank,
        "recommendation": "skip_blank_capture" if is_blank else "proceed_with_layout",
        "is_blank": is_blank,
        "source": "pil_fallback",
    }


def _scene_class(diag: dict[str, Any]) -> str:
    if diag.get("scene_class"):
        return str(diag["scene_class"])
    return str(diag.get("features", {}).get("scene", {}).get("scene_class", "general"))


def _has_ui_signals(diag: dict[str, Any]) -> bool:
    features = diag.get("features", {})
    objects = features.get("objects", {})
    edges = features.get("edges", {})
    colors = features.get("colors", {})
    if objects.get("has_large_objects") or objects.get("many_objects"):
        return True
    if edges.get("text_likelihood"):
        return True
    if colors.get("unique_colors_sampled", 0) >= 8:
        return True
    if edges.get("available") and float(edges.get("edge_density", 0)) > 0.04:
        return True
    return False


def _recommendation(diag: dict[str, Any]) -> str:
    scene_class = _scene_class(diag)
    similarity = diag.get("features", {}).get("similarity", {})
    if similarity.get("match") or scene_class == "unchanged_screen":
        return "skip_unchanged_screen"

    if scene_class == "empty_dark_screen":
        return "skip_blank_capture"

    if scene_class in LOW_VALUE_SCENE_CLASSES and not _has_ui_signals(diag):
        return "skip_blank_capture"

    hint = diag.get("llm_hint", {})
    if hint.get("send_to_llm") and _has_ui_signals(diag):
        return "proceed_with_layout"

    if _has_ui_signals(diag):
        return "proceed_with_layout"

    if scene_class in {"ui_with_text", "ui_blocks", "dense_ui_or_code", "barcode_present"}:
        return "proceed_with_layout"

    return "proceed_low_confidence"
