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
from imgl.catalog import build_interactive_catalog
from imgl.export import (
    default_annotated_path,
    open_image,
    write_annotated_image,
    write_window_preview_images,
)
from imgl.window_scope import apply_discovered_windows, discover_windows, export_window_crop, format_window_picker, summarize_windows
from imgl.interact import run_interactive_shell
from imgl.pipeline import analyze
from imgl.scene_cache import load_or_analyze, save_scene_cache


def _add_output_format_flags(parser: argparse.ArgumentParser) -> None:
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--json", action="store_true", help="Output JSON (default: markdown)")
    group.add_argument("--yaml", action="store_true", help="Output YAML (default: markdown)")


def _output_format(args: argparse.Namespace) -> str:
    from imgl.autodiag import resolve_cli_output_format

    return resolve_cli_output_format(json_flag=args.json, yaml_flag=args.yaml)


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
    parser.add_argument(
        "--max-dim",
        type=int,
        default=None,
        help="Max image dimension for OCR (default: 2560, lower=faster)",
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
        "--portal",
        action="store_true",
        help="Fallback: GNOME portal region picker (after vdisplay mirror fails)",
    )
    capture_parser.add_argument(
        "--interactive",
        action="store_true",
        help="Alias for --portal (deprecated; default uses vdisplay mirror, no dialog)",
    )
    capture_parser.add_argument(
        "--allow-blank",
        action="store_true",
        help="Save capture even when image looks empty/black",
    )
    capture_parser.add_argument(
        "--verify",
        action="store_true",
        help="After capture, verify PNG was updated (portal must not be cancelled)",
    )
    capture_parser.add_argument(
        "--smart",
        action="store_true",
        help="Smart capture with OCR cache clear and X11 fallback",
    )
    capture_parser.add_argument(
        "--analyze",
        action="store_true",
        help="After capture, run OCR/layout analysis and write VQL program",
    )
    capture_parser.add_argument(
        "--vql-out",
        type=Path,
        default=None,
        help="VQL output path for --analyze (default: <png>.vql.json)",
    )
    capture_parser.add_argument(
        "--lang",
        default="eng+pol",
        help="OCR language for --analyze (default: eng+pol)",
    )

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Autodiagnose screenshot (img2nl) + optional vdisplay/vision map",
    )
    doctor_parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="PNG path (default: IMGL_IMAGE or screen.png)",
    )
    doctor_parser.add_argument("--window", default=None, help="Window scope e.g. region-bottom")
    doctor_parser.add_argument(
        "--full",
        action="store_true",
        help="Include vdisplay OS windows + vision correlation",
    )
    doctor_parser.add_argument("--locale", default="pl", help="Summary locale (default: pl)")
    _add_output_format_flags(doctor_parser)

    map_parser = subparsers.add_parser(
        "map",
        help="Map OS windows (vdisplay) to vision regions on screenshot",
    )
    map_parser.add_argument(
        "--image",
        type=Path,
        default=None,
        help="PNG path (default: IMGL_IMAGE or screen.png)",
    )
    map_parser.add_argument("--window", default=None, help="Target window/app to highlight")
    map_parser.add_argument("--locale", default="pl")
    _add_output_format_flags(map_parser)

    execute_parser = subparsers.add_parser(
        "execute",
        help="Run NL UI action (TYPE/KEY/CLICK) with autodiag",
    )
    execute_parser.add_argument("prompt", help='e.g. "wpisz test w Chat input"')
    execute_parser.add_argument("--image", type=Path, default=None, help="Screenshot PNG")
    execute_parser.add_argument("--window", default=None, help="region-bottom, region-top, …")
    execute_parser.add_argument("--dry-run", action="store_true", help="Plan only, no desktop input")
    execute_parser.add_argument(
        "--llm",
        action="store_true",
        help="Vision LLM catalog via OpenRouter (OPENROUTER_API_KEY)",
    )
    execute_parser.add_argument("--no-diagnose", action="store_true", help="Skip capture autodiag")
    execute_parser.add_argument("--locale", default="pl")
    _add_output_format_flags(execute_parser)

    shot_parser = subparsers.add_parser(
        "shot",
        help="capture --interactive + execute (one-shot window control)",
    )
    shot_parser.add_argument("prompt", help='e.g. "wpisz test w Chat input"')
    shot_parser.add_argument("--image", type=Path, default=None, help="Screenshot PNG path")
    shot_parser.add_argument("--window", default=None)
    shot_parser.add_argument("--dry-run", action="store_true")
    shot_parser.add_argument("--llm", action="store_true")
    shot_parser.add_argument("--locale", default="pl")
    _add_output_format_flags(shot_parser)

    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify capture PNG is fresh and valid",
    )
    verify_parser.add_argument(
        "image",
        type=Path,
        nargs="?",
        default=None,
        help="PNG path (default: IMGL_IMAGE or screen.png)",
    )
    verify_parser.add_argument(
        "--before",
        type=float,
        default=None,
        help="Previous mtime to compare (default: file mtime - 1)",
    )

    install_parser = subparsers.add_parser("install", help="Install optional integrations")
    install_sub = install_parser.add_subparsers(dest="install_target", required=True)
    install_sub.add_parser("img2nl", help="pip install img2nl for capture autodiag")
    install_sub.add_parser("vdisplay", help="pip install vdisplay for OS window map")
    install_sub.add_parser("vql", help="pip install vql for portal capture (Wayland)")
    install_sub.add_parser("control", help="pip install nlp2imgl/dsl2imgl/rest2imgl")

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

    interact_parser = subparsers.add_parser(
        "interact",
        help="Interactive shell: list UI elements and pick actions via NL/URI",
    )
    interact_parser.add_argument("image", type=Path, help="Path to screenshot image")
    interact_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("layout.vql.json"),
        help="VQL program path (default: layout.vql.json)",
    )
    interact_parser.add_argument(
        "--lang",
        default="eng+pol",
        help="OCR language(s), e.g. eng+pol (default: eng+pol)",
    )
    interact_parser.add_argument(
        "--allow-blank",
        action="store_true",
        help="Analyze even when img2nl reports empty/blank screen",
    )
    interact_parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute click/type on desktop (requires xdotool or ydotool)",
    )
    interact_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use vision LLM catalog (requires OPENROUTER_API_KEY, pip install litellm)",
    )
    interact_parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Show all OCR/heuristic detections (no noise filter)",
    )
    interact_parser.add_argument(
        "--annotate",
        action="store_true",
        help="Generate numbered overlay image on start (screen.numbered.png)",
    )
    interact_parser.add_argument(
        "--open",
        action="store_true",
        help="Open numbered overlay in default image viewer",
    )
    interact_parser.add_argument(
        "--annotated-output",
        type=Path,
        help="Path for numbered overlay PNG (default: <image>.numbered.png)",
    )
    interact_parser.add_argument(
        "--window",
        help="Analyze only this window id/title (e.g. region-left, region-right)",
    )

    windows_parser = subparsers.add_parser(
        "windows",
        help="Discover windows on screenshot and export per-window crops",
    )
    windows_parser.add_argument("image", type=Path, help="Path to screenshot image")
    windows_parser.add_argument(
        "--lang",
        default="eng+pol",
        help="OCR language(s), e.g. eng+pol (default: eng+pol)",
    )
    windows_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Directory for window crops (default: next to image)",
    )
    windows_parser.add_argument(
        "--export-crops",
        action="store_true",
        help="Write per-window PNG crops",
    )
    windows_parser.add_argument(
        "--annotate",
        action="store_true",
        help="Write numbered preview PNG per window",
    )
    windows_parser.add_argument(
        "--open",
        action="store_true",
        help="Open preview images in default viewer",
    )
    windows_parser.add_argument(
        "--allow-blank",
        action="store_true",
        help="Analyze even when img2nl reports empty/blank screen",
    )

    annotate_parser = subparsers.add_parser(
        "annotate",
        help="Draw numbered overlay on screenshot matching interact catalog",
    )
    annotate_parser.add_argument("image", type=Path, help="Path to screenshot image")
    annotate_parser.add_argument(
        "--lang",
        default="eng+pol",
        help="OCR language(s), e.g. eng+pol (default: eng+pol)",
    )
    annotate_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output PNG path (default: <image>.numbered.png)",
    )
    annotate_parser.add_argument(
        "--allow-blank",
        action="store_true",
        help="Analyze even when img2nl reports empty/blank screen",
    )
    annotate_parser.add_argument(
        "--max-dim",
        type=int,
        default=None,
        help="Max image dimension for OCR (default: 2560, lower=faster)",
    )
    annotate_parser.add_argument(
        "--open",
        action="store_true",
        help="Open result in default image viewer",
    )

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start web UI for manual and autonomous screen control",
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=8008, help="Bind port (default: 8008)")
    serve_parser.add_argument(
        "--work-dir",
        type=Path,
        help="Session directory for captures and layout (default: ~/.imgl/web)",
    )
    serve_parser.add_argument(
        "--image",
        type=Path,
        help="Initial screenshot PNG (optional)",
    )
    serve_parser.add_argument(
        "--execute",
        action="store_true",
        help="Enable desktop execution by default (xdotool/ydotool)",
    )
    serve_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use vision LLM catalog by default",
    )
    serve_parser.add_argument(
        "--capture-on-start",
        action="store_true",
        help="Capture desktop screenshot when server starts",
    )
    serve_parser.add_argument(
        "--window",
        help="Scope catalog to window id (e.g. region-top, region-bottom)",
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

    if args.command == "doctor":
        from imgl.control import default_image_path, run_doctor

        image = args.image or default_image_path()
        text, code = run_doctor(
            image,
            window=args.window,
            full=args.full,
            locale=args.locale,
            output_format=_output_format(args),
        )
        from imgl.terminal_md import print_report

        print_report(text, _output_format(args))
        return code

    if args.command == "map":
        from imgl.control import default_image_path, run_map

        image = args.image or default_image_path()
        text, code = run_map(
            image,
            window=args.window,
            locale=args.locale,
            output_format=_output_format(args),
        )
        from imgl.terminal_md import print_report

        print_report(text, _output_format(args))
        return code

    if args.command == "execute":
        from imgl.control import default_image_path, run_execute

        try:
            text, code = run_execute(
                args.prompt,
                image=args.image or default_image_path(),
                window=args.window,
                dry_run=args.dry_run,
                use_llm=args.llm or None,
                with_diagnostics=not args.no_diagnose,
                locale=args.locale,
                output_format=_output_format(args),
            )
        except (FileNotFoundError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        from imgl.terminal_md import print_report

        print_report(text, _output_format(args))
        return code

    if args.command == "shot":
        from imgl.control import default_image_path, run_shot

        try:
            text, code = run_shot(
                args.prompt,
                image=args.image or default_image_path(),
                window=args.window,
                dry_run=args.dry_run,
                use_llm=args.llm,
                locale=args.locale,
                output_format=_output_format(args),
            )
        except (CaptureError, BlankCaptureError, FileNotFoundError, RuntimeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        from imgl.terminal_md import print_report

        print_report(text, _output_format(args))
        return code

    if args.command == "verify":
        from imgl.control import default_image_path, verify_capture

        image = args.image or default_image_path()
        try:
            path = verify_capture(image, before_mtime=args.before)
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"OK: {path}")
        return 0

    if args.command == "install":
        from imgl.installs import install_control, install_img2nl, install_vdisplay, install_vql

        try:
            if args.install_target == "img2nl":
                install_img2nl()
            elif args.install_target == "vdisplay":
                install_vdisplay()
            elif args.install_target == "vql":
                install_vql()
            elif args.install_target == "control":
                install_control()
            else:
                print(f"Unknown install target: {args.install_target}", file=sys.stderr)
                return 1
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if args.command == "serve":
        try:
            import uvicorn
        except ImportError:
            print(
                "Web server requires: pip install -e '.[web]'",
                file=sys.stderr,
            )
            return 1
        from imgl.web.app import create_app
        from imgl.web.session import WebSettings

        work_dir = args.work_dir or (Path.home() / ".imgl" / "web")
        image_path = args.image
        if image_path is None:
            local_screen = Path.cwd() / "screen.png"
            if local_screen.is_file():
                image_path = local_screen

        settings = WebSettings(
            use_llm=args.llm,
            execute=args.execute,
            selected_window_id=args.window,
        )
        app = create_app(
            work_dir=work_dir,
            image_path=image_path,
            settings=settings,
            auto_select_window=not args.window,
        )
        session = app.state.manager.session
        if args.capture_on_start:
            try:
                session.capture(interactive=True)
                print(f"Captured: {session.image_path}", file=sys.stderr)
            except (BlankCaptureError, CaptureError) as exc:
                print(f"Capture skipped: {exc}", file=sys.stderr)
                if Path(session.image_path).is_file():
                    print(f"Using existing screenshot: {session.image_path}", file=sys.stderr)
                    session.analyze(refresh=False)
                else:
                    print(
                        "No screenshot yet — use 📷 Zrzut ekranu in UI or:\n"
                        "  imgl capture --interactive -o screen.png\n"
                        "  imgl serve --image screen.png",
                        file=sys.stderr,
                    )
        elif image_path and Path(session.image_path).is_file():
            print(f"Loaded screenshot: {session.image_path}", file=sys.stderr)

        print(f"imgl web: http://{args.host}:{args.port}", file=sys.stderr)
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

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

    if args.command == "interact":
        try:
            image_path = resolve_image_path(args.image)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        blank_exit = _check_blank_before_analyze(
            image_path,
            allow_blank=args.allow_blank,
            locale=config.diagnose_locale,
        )
        if blank_exit is not None:
            return blank_exit
        config = _apply_config_overrides(config, args)
        return run_interactive_shell(
            image_path,
            vql_file=args.output,
            lang=args.lang,
            config=config,
            execute=args.execute,
            use_llm=args.llm,
            no_filter=args.no_filter,
            annotate=args.annotate,
            open_annotated=args.open,
            annotated_output=args.annotated_output,
            window=args.window,
        )

    if args.command == "windows":
        try:
            image_path = resolve_image_path(args.image)
        except FileNotFoundError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        blank_exit = _check_blank_before_analyze(
            image_path,
            allow_blank=args.allow_blank,
            locale=config.diagnose_locale,
        )
        if blank_exit is not None:
            return blank_exit
        scene = load_or_analyze(
            image_path,
            vql_file=Path("layout.vql.json"),
            lang=args.lang,
            config=config,
        )
        scene = apply_discovered_windows(scene)
        summaries = summarize_windows(scene, image_path=str(image_path))
        print(format_window_picker(summaries, scene=scene))
        out_dir = args.output_dir or image_path.parent
        paths: list[Path] = []
        if args.export_crops:
            for item in summaries:
                path = export_window_crop(image_path, item.window, output_dir=out_dir)
                paths.append(path)
                print(f"crop: {path}", file=sys.stderr)
        if args.annotate:
            preview_paths = write_window_preview_images(
                scene,
                discover_windows(scene),
                out_dir,
                source_image=image_path,
            )
            paths.extend(preview_paths)
            for path in preview_paths:
                print(f"preview: {path}", file=sys.stderr)
        if args.open:
            for path in paths:
                open_image(path)
        payload = {
            "window_count": len(summaries),
            "windows": [
                {
                    "index": item.index,
                    "id": item.window.id,
                    "title": item.label,
                    "bbox": item.bbox.to_dict(),
                    "interactive_count": item.interactive_count,
                    "element_count": item.element_count,
                }
                for item in summaries
            ],
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    if args.command == "capture":
        from imgl.capture import last_capture_meta
        from imgl.control import capture_interactive, smart_capture

        out = args.output
        before_mtime = out.stat().st_mtime if out and out.is_file() else 0.0
        use_portal = args.portal or args.interactive
        if args.interactive and not args.portal:
            print(
                "Note: --interactive opens GNOME portal; default is vdisplay mirror (no dialog). "
                "Use: imgl capture -o screen.png --verify",
                file=sys.stderr,
            )
        try:
            if args.smart:
                path = smart_capture(out, interactive=use_portal)
            elif args.verify or not use_portal:
                path = capture_interactive(out, verify=args.verify, portal=use_portal)
            else:
                path = capture_screen(
                    args.output,
                    monitor=args.monitor,
                    interactive=use_portal,
                    allow_blank=args.allow_blank,
                    prefer_mirror=True,
                )
        except BlankCaptureError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        except CaptureError as exc:
            print(f"Capture failed: {exc}", file=sys.stderr)
            return 1
        meta = last_capture_meta()
        method = meta.get("method", "unknown")
        print(f"Captured {path} (method={method})", file=sys.stderr)
        if args.analyze:
            from imgl.pipeline import analyze
            from imgl.scene_cache import save_scene_cache

            vql_out = args.vql_out or path.with_suffix(".vql.json")
            scene = analyze(str(path.resolve()), lang=args.lang)
            write_vql_program(scene, vql_out)
            save_scene_cache(scene, vql_out)
            print(f"Analyzed → {vql_out}", file=sys.stderr)
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


def _apply_config_overrides(config: ImglConfig, args) -> ImglConfig:
    max_dim = getattr(args, "max_dim", None)
    if max_dim is not None:
        config.max_dim = max_dim
    return config


def _run_image_command(args, image_path: Path, config: ImglConfig) -> int:
    config = _apply_config_overrides(config, args)
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

    if args.command == "annotate":
        vql_out = Path("layout.vql.json")
        png_out = args.output or default_annotated_path(image_path)
        scene = load_or_analyze(
            image_path,
            vql_file=vql_out,
            lang=args.lang,
            config=config,
        )
        write_vql_program(scene, vql_out)
        save_scene_cache(scene, vql_out)
        catalog = build_interactive_catalog(
            scene,
            image_path=str(image_path),
            vql_file=str(vql_out),
            lang=args.lang,
        )
        path = write_annotated_image(scene, catalog, png_out, source_image=image_path)
        print(f"Wrote {path}", file=sys.stderr)
        print(str(path))
        if args.open:
            if not open_image(path):
                print("Could not open viewer (install xdg-open).", file=sys.stderr)
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
