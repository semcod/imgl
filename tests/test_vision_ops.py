"""IMGL vision_ops and vdisplay_context tests."""

from __future__ import annotations

import io

import pytest

pytest.importorskip("PIL")


def _tiny_png() -> bytes:
    from PIL import Image

    image = Image.new("RGB", (8, 8), color=(255, 0, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def test_match_template_png_finds_exact_copy() -> None:
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    from imgl.vision_ops import match_template_png

    screen = _tiny_png()
    matches = match_template_png(screen, screen, threshold=0.9)
    assert matches
    assert matches[0].confidence >= 0.9


def test_diff_png_bytes_detects_change() -> None:
    from imgl.vision_ops import diff_png_bytes

    before = _tiny_png()
    from PIL import Image

    image = Image.new("RGB", (8, 8), color=(0, 255, 0))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    after = buf.getvalue()
    result = diff_png_bytes(before, after, min_changed_pixels=1)
    assert result["verified"] is True
    assert result["changed_pixels"] > 0


def test_render_match_overlay_png() -> None:
    from imgl.vision_ops import MatchOverlayItem, render_match_overlay_png

    png = _tiny_png()
    overlay = render_match_overlay_png(
        png,
        [
            MatchOverlayItem(
                index=0,
                x=1,
                y=1,
                width=4,
                height=4,
                label="btn",
                confidence=0.95,
                selected=True,
            )
        ],
    )
    assert overlay.startswith(b"\x89PNG")
    assert len(overlay) > len(png)


def test_from_vdisplay_context_metadata_without_image() -> None:
    from imgl.vdisplay_context import from_vdisplay_context

    result = from_vdisplay_context(
        {
            "capture": {"display": ":0", "width": 100, "height": 80},
            "environment": {"routing": {"selected_provider": "vision"}},
            "fingerprint": "abc",
        },
        analyze=False,
    )
    assert result["ok"] is False
    assert result["metadata"]["capture"]["display"] == ":0"
    assert result["metadata"]["routing"]["selected_provider"] == "vision"
