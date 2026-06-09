"""Screenshot capture helpers."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


class CaptureError(RuntimeError):
    """Raised when screen capture fails."""


class BlankCaptureError(CaptureError):
    """Raised when capture succeeded but image is empty/black."""


_last_capture_meta: dict[str, object] = {}


def last_capture_meta() -> dict[str, object]:
    """Metadata from the most recent successful capture (method, display, …)."""
    return dict(_last_capture_meta)


def _prefer_mirror() -> bool:
    raw = os.environ.get("IMGL_CAPTURE_PREFER_MIRROR", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _vql_capture_enabled() -> bool:
    raw = os.environ.get("IMGL_CAPTURE_ALLOW_VQL", "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _portal_fallback_enabled() -> bool:
    """On Wayland, fall back to GNOME portal when driver/mirror capture fails."""
    raw = os.environ.get("IMGL_CAPTURE_PORTAL_FALLBACK", "").strip().lower()
    if raw:
        return raw not in {"0", "false", "no", "off"}
    return _is_wayland()


def _vdisplay_portal_in_chain_enabled() -> bool:
    raw = os.environ.get("IMGL_CAPTURE_VDISPLAY_PORTAL", "").strip().lower()
    if raw:
        return raw not in {"0", "false", "no", "off"}
    return _portal_fallback_enabled()


def default_capture_path(out: str | Path | None = None) -> Path:
    if out:
        path = Path(out).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    path = Path.home() / ".imgl" / "captures" / f"screen_{ts}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _is_wayland() -> bool:
    session = (os.environ.get("XDG_SESSION_TYPE") or "").lower()
    return session == "wayland" or bool(os.environ.get("WAYLAND_DISPLAY"))


def capture_screen(
    out: str | Path | None = None,
    *,
    monitor: int = 1,
    interactive: bool = False,
    allow_blank: bool = False,
    prefer_mirror: bool | None = None,
) -> Path:
    """
    Capture the desktop to a PNG file.

    Priority:
    1. vdisplay mirror / monitor region (no Screen Recording portal)
    2. grim / gnome-screenshot / scrot / mss
    3. vql capture (opt-in: IMGL_CAPTURE_ALLOW_VQL=1)
    4. GNOME portal region picker (only when interactive=True / --portal)
    """
    global _last_capture_meta
    _last_capture_meta = {}
    path = default_capture_path(out)
    errors: list[str] = []
    use_mirror = _prefer_mirror() if prefer_mirror is None else prefer_mirror

    from imgl.installs import ensure_vdisplay

    ensure_vdisplay(quiet=True)

    ok, detail = _try_vdisplay_capture(
        path,
        monitor=monitor,
        allow_blank=allow_blank,
        prefer_mirror=use_mirror,
        allow_portal=False,
    )
    if ok:
        return path
    if detail:
        errors.append(detail)

    if _vdisplay_portal_in_chain_enabled():
        ok, detail = _try_vdisplay_capture(
            path,
            monitor=monitor,
            allow_blank=allow_blank,
            prefer_mirror=False,
            allow_portal=True,
        )
        if ok:
            return path
        if detail:
            errors.append(f"vdisplay-portal: {detail}")

    if interactive:
        if _try_portal_backends(path, allow_blank=allow_blank, errors=errors):
            return path

    for name, runner in _non_portal_backends():
        try:
            result = runner(path)
            if isinstance(result, tuple):
                ok, detail = result
            else:
                ok, detail = bool(result), ""
            if ok:
                if allow_blank or not _is_blank_image(path):
                    from imgl.freshness import mark_capture_fresh

                    mark_capture_fresh(path)
                    _last_capture_meta = {"method": name}
                    return path
                _discard_capture_file(path)
                errors.append(f"{name}: captured but image is blank")
                continue
            errors.append(f"{name}: {detail or 'command failed'}")
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    if not _is_wayland():
        try:
            if _capture_with_mss(path, monitor=monitor):
                if allow_blank or not _is_blank_image(path):
                    _last_capture_meta = {"method": "mss"}
                    return path
                errors.append("mss: captured but image is blank")
        except Exception as exc:
            errors.append(f"mss: {exc}")

    if _vql_capture_enabled():
        if _try_vql_capture(path, monitor=monitor, interactive=False, allow_blank=allow_blank):
            return path
        errors.append("vql: failed or blank")

    if not interactive:
        if _try_portal_backends(path, allow_blank=allow_blank, errors=errors):
            return path

    _discard_capture_file(path)
    hint = _capture_failure_hint(interactive=interactive, errors=errors)
    raise BlankCaptureError(f"{hint}\nTried: {'; '.join(errors) or 'no backends'}")


def _screen_recording_denied(errors: list[str]) -> bool:
    needles = (
        "Screen Recording permission",
        "AccessDenied",
        "Screenshot is not allowed",
        "InteractiveScreenshot is not allowed",
    )
    joined = " ".join(errors)
    return any(n in joined for n in needles)


def _capture_failure_hint(*, interactive: bool, errors: list[str] | None = None) -> str:
    errs = errors or []
    if _screen_recording_denied(errs):
        return (
            "Brak uprawnień Screen Recording w GNOME.\n"
            "Settings → Privacy → Screen Recording → włącz Cursor (lub terminal).\n"
            "Potem: make capture-interactive\n"
            "Jednorazowo z dialogiem: imgl capture --portal -o screen.png --verify"
        )
    if interactive:
        return (
            "Mirror/driver capture failed; portal też nie zadziałał.\n"
            "Wybierz obszar w dialogu GNOME (Settings → Privacy → Screen Recording).\n"
            "Bez portalu: sudo usermod -aG video $USER && re-login (DRM/fbdev)\n"
            "sudo apt install python3-dbus python3-gi grim"
        )
    if _is_wayland():
        return (
            "Screen capture failed on GNOME/Wayland.\n"
            "Portal fallback: imgl capture --portal -o screen.png --verify\n"
            "Bez portalu (driver): sudo usermod -aG video $USER && re-login\n"
            "Multi-monitor mirror: podłącz 2. wyświetlacz lub ustaw wirtualny w GNOME Displays"
        )
    return (
        "Screen capture failed.\n"
        "Try: imgl capture -o screen.png --verify\n"
        "Install: imgl install vdisplay"
    )


def _try_vdisplay_capture(
    path: Path,
    *,
    monitor: int,
    allow_blank: bool,
    prefer_mirror: bool = True,
    allow_portal: bool = False,
) -> tuple[bool, str]:
    """Mirror/region capture via vdisplay; portal only when allow_portal=True."""
    global _last_capture_meta
    try:
        from vdisplay.capture.host import capture_host_to_file
    except ImportError:
        return False, "vdisplay not installed — run: make install-dev (or: imgl install vdisplay)"

    prev_portal = os.environ.get("VDISPLAY_CAPTURE_ALLOW_PORTAL")
    try:
        if allow_portal:
            os.environ["VDISPLAY_CAPTURE_ALLOW_PORTAL"] = "1"
        elif prev_portal is None:
            os.environ.pop("VDISPLAY_CAPTURE_ALLOW_PORTAL", None)
        meta = capture_host_to_file(
            path,
            monitor=monitor,
            display=os.environ.get("DISPLAY"),
            source=os.environ.get("IMGL_CAPTURE_SOURCE"),
            target=os.environ.get("IMGL_CAPTURE_TARGET"),
            prefer_mirror=prefer_mirror,
        )
        if allow_blank or not _is_blank_image(path):
            from imgl.freshness import mark_capture_fresh

            mark_capture_fresh(path)
            _last_capture_meta = dict(meta)
            return True, ""
        _discard_capture_file(path)
        return False, f"vdisplay {meta.get('method', 'capture')}: blank frame"
    except Exception as exc:
        detail = str(exc).strip().replace("\n", " ")
        if len(detail) > 240:
            detail = detail[:237] + "..."
        return False, detail if detail.startswith("vdisplay") else f"vdisplay: {detail}"
    finally:
        if prev_portal is None:
            os.environ.pop("VDISPLAY_CAPTURE_ALLOW_PORTAL", None)
        else:
            os.environ["VDISPLAY_CAPTURE_ALLOW_PORTAL"] = prev_portal


def _try_vql_capture(
    path: Path,
    *,
    monitor: int,
    interactive: bool,
    allow_blank: bool,
) -> bool:
    try:
        from vql.adopt.window import capture_screen as vql_capture
    except ImportError:
        return False

    try:
        info = vql_capture(path, monitor=monitor, interactive=interactive)
        captured = Path(info.path)
        if captured.is_file():
            if captured.resolve() != path.resolve():
                shutil.copy2(captured, path)
            from imgl.freshness import mark_capture_fresh

            mark_capture_fresh(path)
            _last_capture_meta = {"method": "vql", "path": str(captured)}
        target = path if path.is_file() else captured
        if allow_blank or not _is_blank_image(target):
            return True
        _discard_capture_file(path)
    except Exception:
        pass
    return False


def _discard_capture_file(path: Path) -> None:
    """Remove invalid/blank capture so doctor does not read a stale PNG."""
    sidecar = path.with_suffix(".captured_at")
    for candidate in (path, sidecar):
        if candidate.is_file():
            candidate.unlink()


def _non_portal_backends() -> list[tuple[str, callable]]:
    if _is_wayland():
        order = (
            ("gnome-shell", _capture_with_gnome_shell),
            ("grim", _capture_with_grim),
        )
    else:
        order = (
            ("scrot", _capture_with_scrot),
            ("gnome-screenshot", _capture_with_gnome_screenshot),
            ("grim", _capture_with_grim),
        )
    return list(order)


def _portal_backends() -> list[tuple[str, callable]]:
    return [
        ("portal-interactive", lambda p: _capture_with_portal(p, interactive=True)),
        ("portal", lambda p: _capture_with_portal(p, interactive=False)),
    ]


def _try_portal_backends(path: Path, *, allow_blank: bool, errors: list[str]) -> bool:
    global _last_capture_meta
    for name, runner in _portal_backends():
        try:
            result = runner(path)
            if isinstance(result, tuple):
                ok, detail = result
            else:
                ok, detail = bool(result), ""
            if ok:
                if allow_blank or not _is_blank_image(path):
                    from imgl.freshness import mark_capture_fresh

                    mark_capture_fresh(path)
                    _last_capture_meta = {"method": name}
                    return True
                _discard_capture_file(path)
                errors.append(f"{name}: captured but image is blank")
                continue
            errors.append(f"{name}: {detail or 'command failed'}")
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    return False


def _run_command(cmd: list[str], path: Path, *, timeout: int = 20) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    return proc.returncode == 0 and path.is_file() and path.stat().st_size > 0


def _capture_with_gnome_shell(path: Path) -> tuple[bool, str]:
    """GNOME Shell D-Bus screenshot (works on Mutter; grim needs wlroots)."""
    if not shutil.which("gdbus"):
        return False, "gdbus not found"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        path.unlink()
    try:
        proc = subprocess.run(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.Shell.Screenshot",
                "--object-path",
                "/org/gnome/Shell/Screenshot",
                "--method",
                "org.gnome.Shell.Screenshot.Screenshot",
                "false",
                "false",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    if proc.returncode == 0 and path.is_file() and path.stat().st_size > 0:
        return True, ""
    detail = (proc.stderr or proc.stdout or "gnome-shell screenshot failed").strip()
    if "AccessDenied" in detail or "not allowed" in detail.lower():
        return False, (
            "gnome-shell screenshot denied — enable Screen Recording for this app "
            "(GNOME Settings → Privacy → Screen Recording)"
        )
    return False, detail


def _capture_with_grim(path: Path) -> tuple[bool, str]:
    if not shutil.which("grim"):
        return False, "grim not installed"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            ["grim", str(path)],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except Exception as exc:
        return False, str(exc)
    if proc.returncode == 0 and path.is_file() and path.stat().st_size > 0:
        return True, ""
    detail = (proc.stderr or proc.stdout or "grim failed").strip()
    if "wlr-screencopy" in detail:
        detail = "grim unsupported on GNOME/Mutter (use gnome-shell or portal)"
    return False, detail or "command failed"


def _capture_with_gnome_screenshot(path: Path) -> bool:
    if not shutil.which("gnome-screenshot"):
        return False
    return _run_command(["gnome-screenshot", "-f", str(path)], path, timeout=25)


def _capture_with_scrot(path: Path) -> bool:
    if not shutil.which("scrot"):
        return False
    return _run_command(["scrot", str(path)], path)


def _portal_python() -> str:
    """System Python with dbus/gi (venv usually lacks these)."""
    candidates = [
        os.environ.get("VQL_PORTAL_PYTHON", ""),
        "/usr/bin/python3",
        shutil.which("python3") or "",
    ]
    probe = "import dbus; from gi.repository import GLib"
    for exe in candidates:
        if not exe or not Path(exe).is_file():
            continue
        try:
            proc = subprocess.run(
                [exe, "-c", probe],
                capture_output=True,
                timeout=3,
                check=False,
            )
            if proc.returncode == 0:
                return exe
        except Exception:
            continue
    return ""


def _portal_script() -> Path | None:
    try:
        import vql.adopt.portal_capture as mod

        script = Path(mod.__file__)
        if script.is_file():
            return script
    except ImportError:
        pass
    for candidate in (
        Path.home() / "github/oqlos/vql/src/vql/adopt/portal_capture.py",
        Path("/usr/share/vql/portal_capture.py"),
    ):
        if candidate.is_file():
            return candidate
    return None


def _capture_with_portal(path: Path, *, interactive: bool) -> tuple[bool, str]:
    """xdg-desktop-portal screenshot via system python3 + portal_capture.py."""
    py = _portal_python()
    script = _portal_script()
    if not py:
        return False, (
            "portal python (python3-dbus, python3-gi) not found — "
            "sudo apt install python3-dbus python3-gi"
        )
    if not script:
        return False, "portal script missing (install vql or clone oqlos/vql)"

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        path.unlink()

    cmd = [py, str(script), "--out", str(path)]
    if interactive:
        cmd.append("--interactive")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=False)
    except Exception as exc:
        return False, str(exc)

    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        detail = (proc.stderr or proc.stdout or "invalid portal json").strip()
        return False, detail or "portal subprocess failed"

    if not payload.get("ok"):
        detail = str(payload.get("error") or payload.get("hint") or "portal failed")
        return False, detail
    if not path.is_file() or path.stat().st_size < 64:
        return False, "portal succeeded but output file missing"
    return True, ""


def _capture_with_mss(path: Path, *, monitor: int) -> bool:
    import mss
    from PIL import Image

    with mss.mss() as grabber:
        monitors = grabber.monitors
        index = min(max(monitor, 1), len(monitors) - 1)
        shot = grabber.grab(monitors[index])
        image = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        image.save(path)
    return path.is_file()


def _is_blank_image(path: Path) -> bool:
    try:
        from imgl.diagnose import diagnose_content, worth_analyzing

        diag = diagnose_content(path)
        return bool(diag.get("ok")) and not worth_analyzing(diag)
    except Exception:
        from PIL import Image

        image = Image.open(path).convert("RGB")
        small = image.resize((32, 32))
        pixels = list(small.get_flattened_data())
        if not pixels:
            return True
        if len(set(pixels)) <= 1:
            return True
        brightness = [int(0.299 * r + 0.587 * g + 0.114 * b) for r, g, b in pixels]
        return max(brightness) < 8


def capture_status_message(path: Path) -> str | None:
    """Return warning text when a capture looks blank, else None."""
    if _is_blank_image(path):
        return (
            "Capture looks empty or low-content. "
            "Use an existing screenshot, e.g. imgl vql /tmp/screen.png -o layout.vql.json"
        )
    return None
