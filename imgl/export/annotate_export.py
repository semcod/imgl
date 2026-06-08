"""Numbered overlay image for interactive shell catalog."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from imgl.catalog import InteractiveOption
from imgl.paths import resolve_image_path
from imgl.types import BBox, Scene, Window
from imgl.window_scope import crop_window_image, default_window_annotated_path

_CATEGORY_COLORS: dict[str, tuple[str, str]] = {
    "window": ("#2563EB", "#DBEAFE"),
    "button": ("#EA580C", "#FFEDD5"),
    "input": ("#16A34A", "#DCFCE7"),
    "toolbar": ("#6B7280", "#F3F4F6"),
}


def default_annotated_path(image_path: str | Path, *, window_id: str | None = None) -> Path:
    path = Path(image_path)
    if window_id:
        return default_window_annotated_path(path, window_id)
    return path.with_name(f"{path.stem}.numbered{path.suffix or '.png'}")


def scene_to_annotated_image(
    scene: Scene,
    catalog: list[InteractiveOption],
    *,
    source_image: str | Path | None = None,
    window: Window | None = None,
) -> Image.Image:
    """Draw numbered badges and boxes for each catalog option on the screenshot."""
    image_path = source_image or scene.source_image
    if not image_path:
        raise ValueError("source image path required for annotated overlay")

    if window is not None:
        base = crop_window_image(image_path, window).convert("RGBA")
        catalog = _catalog_relative_to_window(catalog, window.bbox)
    else:
        base = Image.open(resolve_image_path(image_path)).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_main, font_small = _load_fonts(base.size)
    badge = _badge_size(base.size)

    for option in catalog:
        stroke, fill = _CATEGORY_COLORS.get(option.category, ("#7C3AED", "#EDE9FE"))
        bbox = option.bbox
        x0, y0 = bbox["x"], bbox["y"]
        x1, y1 = x0 + bbox["w"], y0 + bbox["h"]

        draw.rectangle((x0, y0, x1, y1), outline=stroke, width=max(2, badge // 14))
        draw.rectangle((x0, y0, x1, y1), fill=_hex_rgba(fill, 48))

        label = str(option.index)
        badge_x = max(0, x0)
        badge_y = max(0, y0 - badge - 2)
        if badge_y < 0:
            badge_y = y0 + 2

        _draw_number_badge(
            draw,
            label,
            badge_x,
            badge_y,
            badge=badge,
            stroke=stroke,
            font=font_main,
        )

        hint = _short_hint(option)
        if hint and font_small is not None:
            draw.text(
                (badge_x + badge + 4, badge_y + max(2, badge // 6)),
                hint,
                fill=stroke,
                font=font_small,
            )

    composed = Image.alpha_composite(base, overlay)
    return composed.convert("RGB")


def write_annotated_image(
    scene: Scene,
    catalog: list[InteractiveOption],
    output_path: str | Path,
    *,
    source_image: str | Path | None = None,
    window: Window | None = None,
) -> Path:
    """Save numbered overlay PNG next to the source screenshot."""
    image = scene_to_annotated_image(
        scene,
        catalog,
        source_image=source_image,
        window=window,
    )
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, format="PNG")
    return out.resolve()


def write_window_preview_images(
    scene: Scene,
    windows: list[Window],
    output_dir: str | Path,
    *,
    source_image: str | Path,
) -> list[Path]:
    """Export per-window crops with simple numbered region badges."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, window in enumerate(windows, start=1):
        crop = crop_window_image(source_image, window).convert("RGBA")
        overlay = Image.new("RGBA", crop.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        badge = _badge_size(crop.size)
        font_main, _ = _load_fonts(crop.size)
        _draw_number_badge(
            draw,
            str(index),
            8,
            8,
            badge=badge,
            stroke="#2563EB",
            font=font_main,
        )
        title = window.title or window.id
        draw.rectangle((8, 8 + badge + 6, crop.size[0] - 8, 8 + badge + 34), fill=(37, 99, 235, 180))
        draw.text((16, 8 + badge + 10), _short_hint_text(title, 48), fill="#FFFFFF", font=font_main)
        composed = Image.alpha_composite(crop, overlay).convert("RGB")
        out = out_dir / default_window_annotated_path(source_image, window.id).name
        composed.save(out, format="PNG")
        paths.append(out.resolve())
    return paths


def write_annotated_images_per_window(
    scene: Scene,
    catalogs: dict[str, list[InteractiveOption]],
    *,
    source_image: str | Path,
    output_dir: str | Path | None = None,
) -> dict[str, Path]:
    """Save one numbered overlay per window id."""
    written: dict[str, Path] = {}
    for window in scene.windows:
        catalog = catalogs.get(window.id)
        if not catalog:
            continue
        out = (
            Path(output_dir)
            if output_dir
            else default_window_annotated_path(source_image, window.id)
        )
        if output_dir:
            out = Path(output_dir) / default_window_annotated_path(source_image, window.id).name
        path = write_annotated_image(
            scene,
            catalog,
            out,
            source_image=source_image,
            window=window,
        )
        written[window.id] = path
    return written


def open_image(path: str | Path) -> bool:
    """Open image in the default viewer (xdg-open, open, etc.)."""
    target = str(Path(path).resolve())
    for cmd in (
        ["xdg-open", target],
        ["gio", "open", target],
        ["open", target],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, check=False)
                return True
            except OSError:
                continue
    return False


def _catalog_relative_to_window(
    catalog: list[InteractiveOption],
    origin: BBox,
) -> list[InteractiveOption]:
    shifted: list[InteractiveOption] = []
    for option in catalog:
        bbox = option.bbox
        shifted.append(
            InteractiveOption(
                index=option.index,
                category=option.category,
                element_id=option.element_id,
                element_type=option.element_type,
                label=option.label,
                text=option.text,
                window_id=option.window_id,
                window_title=option.window_title,
                position=(option.position[0] - origin.x, option.position[1] - origin.y),
                bbox={
                    "x": bbox["x"] - origin.x,
                    "y": bbox["y"] - origin.y,
                    "w": bbox["w"],
                    "h": bbox["h"],
                },
                mouse_actions=option.mouse_actions,
                keyboard_actions=option.keyboard_actions,
                primary_action=option.primary_action,
                action_uri=option.action_uri,
                action_payload=option.action_payload,
            )
        )
    return shifted


def _short_hint_text(text: str, max_len: int) -> str:
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _short_hint(option: InteractiveOption, max_len: int = 28) -> str:
    text = option.text or option.label or option.element_type
    text = text.replace("\n", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def _badge_size(image_size: tuple[int, int]) -> int:
    longest = max(image_size)
    return max(22, min(56, int(longest * 0.018)))


def _load_fonts(image_size: tuple[int, int]) -> tuple[ImageFont.ImageFont, ImageFont.ImageFont | None]:
    main_size = max(14, int(_badge_size(image_size) * 0.62))
    small_size = max(11, int(main_size * 0.72))
    try:
        regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        small_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        return (
            ImageFont.truetype(regular, main_size),
            ImageFont.truetype(small_path, small_size),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default


def _draw_number_badge(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    *,
    badge: int,
    stroke: str,
    font: ImageFont.ImageFont,
) -> None:
    box = (x, y, x + badge, y + badge)
    draw.rectangle(box, fill=stroke, outline="#FFFFFF", width=2)
    tw, th = _text_size(draw, text, font)
    draw.text(
        (x + (badge - tw) // 2, y + (badge - th) // 2 - 1),
        text,
        fill="#FFFFFF",
        font=font,
    )


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    if hasattr(draw, "textbbox"):
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    return draw.textsize(text, font=font)  # type: ignore[attr-defined]


def _hex_rgba(hex_color: str, alpha: int) -> tuple[int, int, int, int]:
    color = hex_color.lstrip("#")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return (r, g, b, alpha)
