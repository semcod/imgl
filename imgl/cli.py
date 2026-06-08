"""Command-line interface for imgl."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import json

from imgl import __version__
from imgl.actions import actions
from imgl.capture import BlankCaptureError, CaptureError, capture_screen
from imgl.config import ImglConfig
from imgl.diagnose import BlankImageError, diagnose_content, worth_analyzing
from imgl.export import scene_to_html, scene_to_json, scene_to_svg, scene_to_vql_json, write_vql_program
from imgl.paths import resolve_image_path
from imgl.pipeline import analyze


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("image", type=Path, help="Path to screenshot image")
    parser.add_argument(
        "--lang",
        default="eng+pol",
        help="OCR language(s), e.g. eng+pol (default: eng+pol)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write output to file (default: stdout)",
    )
    parser.add_argument(
        "--allow-blank",
        action="store_true",
        help="Analyze even when img2nl reports empty/blank screen",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imgl",
        description="Screenshot to semantic UI layout (JSON/HTML/SVG)",
    )
    parser.add_argument("--version", action="version", version=f"imgl {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a screenshot to JSON")
    _add_common_args(analyze_parser)
    analyze_parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON (default for analyze)",
    )

    html_parser = subparsers.add_parser("html", help="Analyze and export HTML layout")
    _add_common_args(html_parser)
    html_parser.add_argument(
        "--embed-image",
        action="store_true",
        help="Embed source screenshot as background image",
    )

    svg_parser = subparsers.add_parser("svg", help="Analyze and export SVG layout")
    _add_common_args(svg_parser)
    svg_parser.add_argument(
        "--mode",
        choices=["wireframe", "overlay"],
        default="wireframe",
        help="SVG render mode (default: wireframe)",
    )
    svg_parser.add_argument(
        "--background",
        type=Path,
        help="Background image for overlay mode (default: source screenshot)",
    )

    vql_parser = subparsers.add_parser("vql", help="Analyze and export VQL program JSON")
    _add_common_args(vql_parser)
    vql_parser.add_argument(
        "--with-grid",
        action="store_true",
        help="Include screen_regions color grid layer (requires vql package)",
    )
    vql_parser.add_argument(
        "--grid",
        type=int,
        default=12,
        help="Grid size for color regions (default: 12)",
    )

    find_parser = subparsers.add_parser("find", help="Find elements and emit actions")
    _add_common_args(find_parser)
    find_parser.add_argument(
        "--type",
        dest="element_type",
        help="Element type: button, input, label, text, ...",
    )
    find_parser.add_argument("--text", help="Match element text")
    find_parser.add_argument("--label", help="Match input label")
    find_parser.add_argument("--window", help="Limit to window title or id")
    find_parser.add_argument(
        "--click",
        action="store_true",
        help="Emit click action for first match",
    )
    find_parser.add_argument(
        "--type-into",
        dest="type_into",
        metavar="VALUE",
        help="Emit type action for input matching --label/--text",
    )
    find_parser.add_argument(
        "--list",
        action="store_true",
        help="List all click/type actions in scene",
    )

    capture_parser = subparsers.add_parser("capture", help="Capture desktop screenshot to PNG")
    capture_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("screen.png"),
        help="Output PNG path (default: screen.png)",
    )
    capture_parser.add_argument("--monitor", type=int, default=1, help="Monitor index (default: 1)")
    capture_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive portal capture (GNOME/Wayland permission prompt)",
    )
    capture_parser.add_argument(
        "--allow-blank",
        action="store_true",
        help="Save capture even when image looks empty/black",
    )

    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Check if image has meaningful content (img2nl)",
    )
    diagnose_parser.add_argument("image", type=Path, help="Path to screenshot image")
    diagnose_parser.add_argument(
        "--locale",
        default="pl",
        help="Summary language for img2nl (default: pl)",
    )
    diagnose_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write JSON output to file (default: stdout)",
    )

    return parser


def _write_output(content: str, output: Path | None) -> None:
    if output:
        output.write_text(content, encoding="utf-8")
        print(f"Wrote {output}", file=sys.stderr)
    else:
        print(content)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = ImglConfig()

    if args.command == "diagnose":
        try:
            image_path = resolve_image_path(args.image)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        diag = diagnose_content(image_path, locale=args.locale)
        payload = {
            "ok": diag.get("ok", False),
            "path": str(image_path),
            "worth_analyzing": worth_analyzing(diag) if diag.get("ok") else False,
            "is_blank": diag.get("is_blank", False),
            "scene_class": diag.get("scene_class", ""),
            "recommendation": diag.get("recommendation", ""),
            "summary": diag.get("text", ""),
            "source": diag.get("source", ""),
            "llm_hint": diag.get("llm_hint", {}),
            "error": diag.get("error"),
        }
        _write_output(json.dumps(payload, indent=2, ensure_ascii=False), args.output)
        return 0 if payload["ok"] else 1

    if args.command == "capture":
        try:
            path = capture_screen(
                args.output,
                monitor=args.monitor,
                interactive=args.interactive,
                allow_blank=args.allow_blank,
            )
        except BlankCaptureError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except CaptureError as exc:
            print(f"Capture failed: {exc}", file=sys.stderr)
            return 1
        print(f"Captured {path}", file=sys.stderr)
        print(str(path.resolve()))
        return 0

    try:
        image_path = resolve_image_path(args.image)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    try:
        return _run_image_command(args, image_path, config)
    except BlankImageError as exc:
        print(f"Blank image: {exc}", file=sys.stderr)
        print("Run: imgl diagnose <image>  or  imgl capture --interactive", file=sys.stderr)
        return 2


def _check_blank_before_analyze(
    image_path: Path,
    *,
    allow_blank: bool,
    locale: str,
) -> int | None:
    if allow_blank:
        return None
    diag = diagnose_content(image_path, locale=locale)
    if diag.get("ok") and not worth_analyzing(diag):
        print(diag.get("text") or diag.get("summary", "Blank or empty screen"), file=sys.stderr)
        print(
            "Aborted: image has no meaningful content. "
            "Use a real screenshot (e.g. /tmp/screen.png) or pass --allow-blank.",
            file=sys.stderr,
        )
        return 2
    return None


def _run_image_command(args, image_path: Path, config: ImglConfig) -> int:
    blank_exit = _check_blank_before_analyze(
        image_path,
        allow_blank=getattr(args, "allow_blank", False),
        locale=config.diagnose_locale,
    )
    if blank_exit is not None:
        return blank_exit

    if args.command == "analyze":
        scene = analyze(image_path, lang=args.lang, config=config)
        _write_output(scene_to_json(scene), args.output)
        return 0

    if args.command == "html":
        scene = analyze(image_path, lang=args.lang, config=config)
        html = scene_to_html(scene, embed_image=args.embed_image)
        _write_output(html, args.output)
        return 0

    if args.command == "svg":
        scene = analyze(image_path, lang=args.lang, config=config)
        background = None
        if args.mode == "overlay":
            background = str(args.background or image_path)
        svg = scene_to_svg(scene, mode=args.mode, background=background)
        _write_output(svg, args.output)
        return 0

    if args.command == "vql":
        scene = analyze(image_path, lang=args.lang, config=config)
        if args.output:
            write_vql_program(
                scene,
                args.output,
                include_grid=args.with_grid,
                grid=args.grid,
            )
            print(f"Wrote {args.output}", file=sys.stderr)
        else:
            _write_output(
                scene_to_vql_json(scene, include_grid=args.with_grid, grid=args.grid),
                None,
            )
        return 0

    if args.command == "find":
        scene = analyze(image_path, lang=args.lang, config=config)
        finder = actions(scene)

        if args.list:
            payload = finder.list_actions()
        elif args.click:
            payload = finder.click(
                args.element_type,
                text=args.text,
                label=args.label,
                window=args.window,
            )
        elif args.type_into is not None:
            payload = finder.type_into(
                args.type_into,
                label=args.label,
                text=args.text,
                window=args.window,
            )
        else:
            matches = finder.find(
                args.element_type,
                text=args.text,
                label=args.label,
                window=args.window,
            )
            payload = [
                {
                    "element_id": target.element.id,
                    "element_type": target.element.type,
                    "text": target.element.text,
                    "window_id": target.window.id if target.window else None,
                    "click_coords": list(target.click_coords()),
                    "bbox": target.element.bbox.to_dict(),
                }
                for target in matches
            ]

        _write_output(json.dumps(payload, indent=2, ensure_ascii=False), args.output)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
