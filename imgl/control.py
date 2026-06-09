"""Window control CLI — capture, doctor, execute, shot (replaces Makefile workflow)."""

from __future__ import annotations

import os
from pathlib import Path

from imgl.autodiag import diagnose_capture, render_report
from imgl.capture import BlankCaptureError, CaptureError, capture_screen
from imgl.diagnose import diagnose_content, worth_analyzing
from imgl.freshness import clear_vql_cache, is_valid_png, mark_capture_fresh, verify_capture_updated


def default_image_path() -> Path:
    for key in ("IMGL_IMAGE", "KORU_IMGL_IMAGE"):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw).expanduser()
    local = Path.cwd() / "screen.png"
    return local


def default_window() -> str | None:
    for key in ("IMGL_WINDOW", "KORU_IMGL_WINDOW"):
        raw = os.environ.get(key, "region-bottom").strip()
        if raw:
            return raw
    return None


def _vql_cache_paths(image: Path) -> list[Path]:
    return [
        image.with_suffix(".vql.imgl.json"),
        image.with_suffix(".vql.json"),
    ]


def clear_ocr_cache(image: Path) -> list[str]:
    return clear_vql_cache(image)


def screen_usable(image: Path, *, locale: str = "pl") -> bool:
    if not is_valid_png(image):
        return False
    return worth_analyzing(diagnose_content(image, locale=locale))


def smart_capture(
    image: str | Path | None = None,
    *,
    interactive: bool = False,
    locale: str = "pl",
) -> Path:
    """Capture with cache invalidation and optional vdisplay X11 fallback."""
    path = Path(image).expanduser() if image else default_image_path()
    caches = _vql_cache_paths(path)
    if path.is_file() and any(cache.is_file() and path.stat().st_mtime > cache.stat().st_mtime for cache in caches):
        clear_ocr_cache(path)

    if screen_usable(path, locale=locale) and any(cache.is_file() for cache in caches):
        return path

    if screen_usable(path, locale=locale):
        clear_ocr_cache(path)

    clear_ocr_cache(path)
    try:
        capture_screen(path, interactive=interactive, prefer_mirror=True)
    except (BlankCaptureError, CaptureError):
        if interactive:
            raise

    if is_valid_png(path) and screen_usable(path, locale=locale):
        mark_capture_fresh(path)
        return path

    if not interactive:
        try:
            from vdisplay.capture.linux_xwd import capture_display_png
            from vdisplay.discovery import resolve_host_display
        except ImportError:
            resolve_host_display = None  # type: ignore[assignment]

        if resolve_host_display is not None:
            display = resolve_host_display()
            data = capture_display_png(display)
            if len(data) >= 64 and data[:8] == b"\x89PNG\r\n\x1a\n":
                path.write_bytes(data)
                mark_capture_fresh(path)
                if screen_usable(path, locale=locale):
                    return path

    fallback = Path.cwd() / "screen.png"
    if fallback.resolve() != path.resolve() and is_valid_png(fallback) and screen_usable(fallback, locale=locale):
        clear_ocr_cache(path)
        path.write_bytes(fallback.read_bytes())
        fb_cache = fallback.with_suffix(".vql.imgl.json")
        if fb_cache.is_file():
            path.with_suffix(".vql.imgl.json").write_bytes(fb_cache.read_bytes())
        mark_capture_fresh(path)
        return path

    if interactive:
        raise CaptureError(
            "Capture failed — wybierz obszar w portalu GNOME (nie anuluj)."
        )
    raise CaptureError(
        "Capture failed. Na GNOME/Wayland: imgl capture --interactive -o "
        f"{path}"
    )


def capture_interactive(
    image: str | Path | None = None,
    *,
    verify: bool = True,
    locale: str = "pl",
    portal: bool = False,
) -> Path:
    """Capture via vdisplay mirror (no GNOME consent). Portal only when portal=True."""
    from imgl.installs import ensure_vdisplay

    ensure_vdisplay(quiet=True)
    path = Path(image).expanduser() if image else default_image_path()
    before_mtime = path.stat().st_mtime if path.is_file() else 0.0
    clear_ocr_cache(path)
    sidecar = path.with_suffix(".captured_at")
    if sidecar.is_file():
        sidecar.unlink()

    before_size = path.stat().st_size if path.is_file() else 0
    from imgl.capture import _is_wayland, _portal_fallback_enabled

    use_portal = portal or (_portal_fallback_enabled() and _is_wayland())
    try:
        captured = capture_screen(path, interactive=use_portal, prefer_mirror=True)
    except BlankCaptureError:
        if use_portal:
            raise
        if _portal_fallback_enabled():
            import sys

            print(
                "Mirror/driver capture unavailable — fallback: GNOME portal "
                "(wybierz obszar; jednorazowa zgoda Screen Recording).",
                file=sys.stderr,
            )
            captured = capture_screen(path, interactive=True, prefer_mirror=False)
        else:
            raise
    if (
        before_mtime
        and captured.is_file()
        and captured.stat().st_mtime <= before_mtime
        and captured.stat().st_size == before_size
    ):
        raise CaptureError(
            f"Capture did not update {captured} — retry or use: imgl capture --portal"
        )
    if not is_valid_png(captured):
        raise CaptureError(
            f"Capture produced invalid PNG ({captured.stat().st_size} bytes): {captured}"
        )
    mark_capture_fresh(captured)
    clear_ocr_cache(captured)
    if verify:
        verify_capture_updated(captured, before_mtime)
    return captured


def verify_capture(image: str | Path | None = None, *, before_mtime: float | None = None) -> Path:
    path = Path(image).expanduser() if image else default_image_path()
    before = before_mtime if before_mtime is not None else (
        path.stat().st_mtime - 1 if path.is_file() else 0.0
    )
    verify_capture_updated(path, before)
    return path


def run_doctor(
    image: str | Path | None = None,
    *,
    window: str | None = None,
    full: bool = False,
    locale: str = "pl",
    output_format: str = "markdown",
) -> tuple[str, int]:
    img = str(image) if image else str(default_image_path())
    win = window if window is not None else default_window()

    if full:
        from imgl.vdisplay_bridge import build_window_control_report

        report = build_window_control_report(img, window=win, locale=locale)
        capture = report.get("capture") or {}
    else:
        capture = diagnose_capture(img, locale=locale)
        report = {"capture": capture, "verdict": capture.get("verdict")}

    text = render_report(report, output_format)
    ok = capture.get("verdict") in {"real_ui", "uncertain"} and capture.get("is_fresh", True)
    return text, 0 if ok else 1


def run_map(
    image: str | Path | None = None,
    *,
    window: str | None = None,
    locale: str = "pl",
    output_format: str = "markdown",
) -> tuple[str, int]:
    from imgl.vdisplay_bridge import build_window_control_report

    img = str(image) if image else str(default_image_path())
    win = window if window is not None else default_window()
    report = build_window_control_report(img, window=win, locale=locale)
    return render_report(report, output_format), 0


def _control_packages_present() -> bool:
    pkg_root = Path(__file__).resolve().parents[1] / "packages"
    return (pkg_root / "dsl2imgl").is_dir() and (pkg_root / "nlp2imgl").is_dir()


def _require_nlp2imgl():
    try:
        from nlp2imgl.control import apply_nl_with_diag

        return apply_nl_with_diag
    except ImportError as first_exc:
        if _control_packages_present():
            try:
                from imgl.installs import install_control

                install_control()
                from nlp2imgl.control import apply_nl_with_diag

                return apply_nl_with_diag
            except Exception as install_exc:
                raise RuntimeError(
                    "Control layer install failed. Run: imgl install control "
                    f"— {install_exc}"
                ) from install_exc
        raise RuntimeError(
            "Install control layer: imgl install control "
            "(dsl2imgl + nlp2imgl + rest2imgl + cli2imgl; "
            "pip install -e . alone is not enough) "
            f"— {first_exc}"
        ) from first_exc


def run_execute(
    prompt: str,
    *,
    image: str | Path | None = None,
    window: str | None = None,
    dry_run: bool = False,
    use_llm: bool | None = None,
    with_diagnostics: bool = True,
    locale: str = "pl",
    output_format: str = "markdown",
) -> tuple[str, int]:
    apply_nl_with_diag = _require_nlp2imgl()
    img = str(image) if image else str(default_image_path())
    if not Path(img).is_file():
        raise FileNotFoundError(f"screenshot missing: {img} — run: imgl capture --interactive -o {img}")

    if use_llm:
        from imgl.llm_catalog import _load_env_files

        _load_env_files()
        if not os.environ.get("OPENROUTER_API_KEY", "").strip():
            raise RuntimeError(
                "Brak OPENROUTER_API_KEY — export klucza lub dodaj do .env "
                "(cwd lub katalog projektu imgl)"
            )

    win = window if window is not None else default_window()
    if use_llm is None:
        raw = os.environ.get("IMGL_USE_LLM", "").strip().lower()
        use_llm = raw in {"1", "true", "yes", "on"}

    payload = apply_nl_with_diag(
        prompt,
        image=img,
        window=win,
        execute=not dry_run,
        dry_run=dry_run,
        with_diagnostics=with_diagnostics,
        use_llm=use_llm,
        locale=locale,
    )

    if output_format == "json":
        import json

        text = json.dumps(payload, ensure_ascii=False, indent=2)
    elif payload.get("diagnostics"):
        text = render_report(payload["diagnostics"], output_format)  # type: ignore[arg-type]
    else:
        import json

        text = json.dumps(payload, ensure_ascii=False, indent=2)

    checks = (payload.get("diagnostics") or {}).get("checks") or {}
    ok = bool(payload.get("ok")) and not checks.get("blocked_stale_capture")
    return text, 0 if ok else 1


def run_shot(
    prompt: str,
    *,
    image: str | Path | None = None,
    window: str | None = None,
    dry_run: bool = False,
    use_llm: bool = False,
    locale: str = "pl",
    output_format: str = "markdown",
) -> tuple[str, int]:
    path = capture_interactive(image, verify=True, locale=locale)
    return run_execute(
        prompt,
        image=path,
        window=window,
        dry_run=dry_run,
        use_llm=use_llm,
        locale=locale,
        output_format=output_format,
    )


def install_img2nl() -> None:
    from imgl.installs import install_img2nl as _install

    _install()


def install_vdisplay() -> None:
    from imgl.installs import install_vdisplay as _install

    _install()


__all__ = [
    "capture_interactive",
    "clear_ocr_cache",
    "default_image_path",
    "default_window",
    "install_img2nl",
    "install_vdisplay",
    "run_doctor",
    "run_execute",
    "run_map",
    "run_shot",
    "smart_capture",
    "verify_capture",
]
