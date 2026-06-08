"""Optional vision-LLM refinement for interactive element catalogs."""

from __future__ import annotations

import base64
import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from imgl.catalog import InteractiveOption, build_interactive_catalog
from imgl.types import BBox, Scene, Window
from imgl.uri import uri_for_imgl_click
from imgl.window_scope import crop_window_image, scene_for_window

DEFAULT_VISION_MODEL = "openrouter/google/gemini-2.5-flash"

_SYSTEM_PROMPT = """You analyze desktop screenshots and list ONLY truly interactive UI elements
that a user can click or type into (buttons, links, tabs, menus, text fields, search boxes).
Ignore plain text, code lines, labels, icons without clear affordance, and window chrome noise.

Return strict JSON:
{
  "elements": [
    {
      "label": "short visible name",
      "type": "button|input|link|tab|menu",
      "x_pct": 0.0-1.0,
      "y_pct": 0.0-1.0,
      "confidence": 0.0-1.0
    }
  ]
}
Max 25 elements. x_pct/y_pct = center of clickable area, normalized to image size."""


def _env_file_candidates() -> list[Path]:
    """Prefer cwd .env, then package/project root .env (no parent walk)."""
    here = Path(__file__).resolve()
    return [
        Path.cwd() / ".env",
        here.parents[1] / ".env",
    ]


def _load_env_files() -> None:
    """Load OPENROUTER_API_KEY from .env when not exported in shell."""
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return

    for candidate in _env_file_candidates():
        if not candidate.is_file():
            continue
        try:
            from dotenv import load_dotenv

            load_dotenv(candidate, override=False)
        except ImportError:
            for line in candidate.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                if key.strip() == "OPENROUTER_API_KEY" and value.strip():
                    os.environ["OPENROUTER_API_KEY"] = value.strip().strip('"').strip("'")
                    break
        if os.getenv("OPENROUTER_API_KEY", "").strip():
            return


def llm_available() -> bool:
    _load_env_files()
    return bool(os.getenv("OPENROUTER_API_KEY", "").strip())


def llm_dependencies_ok() -> tuple[bool, str | None]:
    try:
        import litellm  # type: ignore  # noqa: F401
    except ImportError:
        return False, "litellm not installed (pip install -e '.[llm]')"
    return True, None


def refine_catalog_with_llm(
    scene: Scene,
    *,
    image_path: str,
    vql_file: str = "layout.vql.json",
    lang: str = "eng",
    model: str | None = None,
    max_elements: int = 25,
    window: Window | None = None,
) -> tuple[list[InteractiveOption], dict[str, Any]]:
    """
    Use a vision LLM to build a cleaner interactive catalog.

    Falls back to filtered heuristic catalog when LLM is unavailable or fails.
    """
    resolved_model = model or os.getenv("IMGL_VISION_MODEL", DEFAULT_VISION_MODEL)
    meta: dict[str, Any] = {"source": "heuristic", "model": resolved_model}
    if window is not None:
        meta["window_id"] = window.id
        meta["window_title"] = window.title

    deps_ok, deps_error = llm_dependencies_ok()
    if not deps_ok:
        meta["error"] = deps_error
        return _heuristic_fallback(
            scene,
            image_path=image_path,
            vql_file=vql_file,
            lang=lang,
            window=window,
        ), meta

    if not llm_available():
        meta["error"] = "OPENROUTER_API_KEY not set (export it or add to .env)"
        return _heuristic_fallback(
            scene,
            image_path=image_path,
            vql_file=vql_file,
            lang=lang,
            window=window,
        ), meta

    try:
        scoped_scene = scene_for_window(scene, window) if window is not None else scene
        crop_bbox = window.bbox if window is not None else None
        raw = _call_vision_llm(
            image_path,
            model=resolved_model,
            max_elements=max_elements,
            crop_bbox=crop_bbox,
            window_title=window.title if window is not None else None,
        )
        options = _llm_json_to_options(
            raw,
            scene=scoped_scene,
            image_path=image_path,
            vql_file=vql_file,
            lang=lang,
            origin_x=window.bbox.x if window is not None else 0,
            origin_y=window.bbox.y if window is not None else 0,
            window=window,
        )
        options = _snap_options_to_scene(options, scene, window=window)
        if options:
            meta["source"] = "llm"
            meta["element_count"] = len(options)
            return options, meta
        meta["error"] = "LLM returned no elements"
    except Exception as exc:
        meta["error"] = _short_error(exc)

    return _heuristic_fallback(
        scene,
        image_path=image_path,
        vql_file=vql_file,
        lang=lang,
        window=window,
    ), meta


def _heuristic_fallback(
    scene: Scene,
    *,
    image_path: str,
    vql_file: str,
    lang: str,
    window: Window | None = None,
) -> list[InteractiveOption]:
    from imgl.catalog_filter import filter_catalog

    base = build_interactive_catalog(
        scene,
        image_path=image_path,
        vql_file=vql_file,
        lang=lang,
        filter_noise=False,
        window_id=window.id if window is not None else None,
    )
    return filter_catalog(base)


def _short_error(exc: Exception) -> str:
    text = str(exc).strip()
    if len(text) > 220:
        return text[:217] + "..."
    return text or exc.__class__.__name__


def _call_vision_llm(
    image_path: str,
    *,
    model: str,
    max_elements: int,
    crop_bbox: BBox | None = None,
    window_title: str | None = None,
) -> dict[str, Any]:
    import litellm  # type: ignore

    litellm.set_verbose = False
    image_b64 = _image_to_base64(image_path, crop_bbox=crop_bbox)
    scope_hint = (
        f"This image shows one application window{f' ({window_title})' if window_title else ''}. "
        "Coordinates are relative to this cropped window only."
    )
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                },
                {
                    "type": "text",
                    "text": (
                        f"{scope_hint} "
                        f"List up to {max_elements} interactive elements. "
                        "Prefer navigation tabs, search fields, primary buttons, and form inputs."
                    ),
                },
            ],
        },
    ]
    response = litellm.completion(
        model=model,
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = (response.choices[0].message.content or "").strip()
    return _parse_json_payload(content)


def _parse_json_payload(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def _image_to_base64(
    image_path: str,
    *,
    max_dim: int = 1536,
    crop_bbox: BBox | None = None,
) -> str:
    if crop_bbox is not None:
        image = crop_window_image(image_path, Window(id="crop", bbox=crop_bbox, title=None, z=0))
    else:
        image = Image.open(image_path).convert("RGB")
    w, h = image.size
    longest = max(w, h)
    if longest > max_dim:
        scale = max_dim / longest
        image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    buf = BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _llm_json_to_options(
    payload: dict[str, Any],
    *,
    scene: Scene,
    image_path: str,
    vql_file: str,
    lang: str,
    origin_x: int = 0,
    origin_y: int = 0,
    window: Window | None = None,
) -> list[InteractiveOption]:
    elements = payload.get("elements") or []
    options: list[InteractiveOption] = []
    width = max(1, scene.width)
    height = max(1, scene.height)

    for index, item in enumerate(elements, start=1):
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        if not label:
            continue
        try:
            x_pct = float(item["x_pct"])
            y_pct = float(item["y_pct"])
        except (KeyError, TypeError, ValueError):
            continue
        x = origin_x + int(round(x_pct * width))
        y = origin_y + int(round(y_pct * height))
        element_type = str(item.get("type") or "button").lower()
        category = "input" if element_type == "input" else "button"
        bbox = {
            "x": max(0, x - 40),
            "y": max(0, y - 14),
            "w": 80,
            "h": 28,
        }
        element_id = f"llm-{index}"
        click_payload = {
            "action": "click",
            "x": x,
            "y": y,
            "element_id": element_id,
            "element_type": category,
            "text": label,
            "window_id": window.id if window is not None else None,
            "bbox": bbox,
        }
        options.append(
            InteractiveOption(
                index=index,
                category=category,
                element_id=element_id,
                element_type=category,
                label=label,
                text=label,
                window_id=window.id if window is not None else None,
                window_title=window.title if window is not None else None,
                position=(x, y),
                bbox=bbox,
                mouse_actions=[f"LPM ({x}, {y}) — {label}"],
                keyboard_actions=["LLM vision detection"],
                primary_action="click",
                action_uri=uri_for_imgl_click(
                    image=image_path,
                    file=vql_file,
                    text=label,
                    element_id=element_id,
                    window=window.id if window is not None else None,
                    lang=lang,
                ),
                action_payload=click_payload,
            )
        )
    return options


def _snap_options_to_scene(
    options: list[InteractiveOption],
    scene: Scene,
    *,
    window: Window | None = None,
) -> list[InteractiveOption]:
    """Align LLM centers to nearest OCR/detected elements when labels match."""
    if not scene.source_image:
        return options

    candidates = build_interactive_catalog(
        scene,
        image_path=scene.source_image,
        filter_noise=False,
        window_id=window.id if window is not None else None,
    )
    if not candidates:
        return options

    snapped: list[InteractiveOption] = []
    for index, option in enumerate(options, start=1):
        match = _best_label_match(option.label, candidates)
        if match is None:
            option.index = index
            snapped.append(option)
            continue
        payload = dict(match.action_payload)
        payload["text"] = option.label
        payload["llm_snapped_from"] = option.element_id
        snapped.append(
            InteractiveOption(
                index=index,
                category=match.category,
                element_id=match.element_id,
                element_type=match.element_type,
                label=option.label,
                text=option.label,
                window_id=match.window_id,
                window_title=match.window_title,
                position=match.position,
                bbox=match.bbox,
                mouse_actions=match.mouse_actions,
                keyboard_actions=["LLM + OCR snap"],
                primary_action=match.primary_action,
                action_uri=match.action_uri,
                action_payload=payload,
            )
        )
    return snapped


def _best_label_match(
    label: str,
    candidates: list[InteractiveOption],
) -> InteractiveOption | None:
    query = label.casefold().strip()
    if not query:
        return None

    best: tuple[float, InteractiveOption] | None = None
    for candidate in candidates:
        if candidate.category == "window":
            continue
        for text in (candidate.text, candidate.label):
            if not text:
                continue
            cand = text.casefold().strip()
            if query == cand:
                return candidate
            if query in cand or cand in query:
                score = min(len(query), len(cand)) / max(len(query), len(cand))
                if best is None or score > best[0]:
                    best = (score, candidate)
    return best[1] if best and best[0] >= 0.45 else None
