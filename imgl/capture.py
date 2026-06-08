"""Screenshot capture helpers."""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


class CaptureError(RuntimeError):
    """Raised when screen capture fails."""


class BlankCaptureError(CaptureError):
    """Raised when capture succeeded but image is empty/black."""


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
) -> Path:
    """
    Capture the desktop to a PNG file.

    Tries vql capture (if installed), then grim/gnome-screenshot/scrot.
    On Wayland, mss is avoided (usually returns a black frame).
    """
    path = default_capture_path(out)
    errors: list[str] = []

    if _try_vql_capture(path, monitor=monitor, interactive=interactive, allow_blank=allow_blank):
        return path

    for name, runner in _native_backends(interactive=interactive):
        try:
            if runner(path):
                if allow_blank or not _is_blank_image(path):
                    return path
                errors.append(f"{name}: captured but image is blank")
                continue
            errors.append(f"{name}: command failed")
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    if not _is_wayland():
        try:
            if _capture_with_mss(path, monitor=monitor):
                if allow_blank or not _is_blank_image(path):
                    return path
                errors.append("mss: captured but image is blank")
        except Exception as exc:
            errors.append(f"mss: {exc}")

    hint = (
        "Screen capture failed or produced a blank image (common on GNOME/Wayland). "
        "Try: imgl capture --interactive  OR use an existing PNG:\n"
        "  imgl vql /tmp/screen.png -o layout.vql.json\n"
        "Install vql for portal capture: pip install -e ~/github/oqlos/vql"
    )
    raise BlankCaptureError(f"{hint}\nTried: {'; '.join(errors) or 'no backends'}")


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
        if allow_blank or not _is_blank_image(captured):
            return True
    except Exception:
        pass
    return False


def _native_backends(*, interactive: bool) -> list[tuple[str, callable]]:
    backends: list[tuple[str, callable]] = []

    if interactive:
        portal = _capture_with_portal
        backends.append(("portal-interactive", lambda p: portal(p, interactive=True)))

    if _is_wayland():
        order = (
            ("gnome-screenshot", _capture_with_gnome_screenshot),
            ("scrot", _capture_with_scrot),
            ("grim", _capture_with_grim),
        )
    else:
        order = (
            ("scrot", _capture_with_scrot),
            ("gnome-screenshot", _capture_with_gnome_screenshot),
            ("grim", _capture_with_grim),
        )
    backends.extend(order)
    return backends


def _run_command(cmd: list[str], path: Path, *, timeout: int = 20) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    return proc.returncode == 0 and path.is_file() and path.stat().st_size > 0


def _capture_with_grim(path: Path) -> bool:
    if not shutil.which("grim"):
        return False
    return _run_command(["grim", str(path)], path)


def _capture_with_gnome_screenshot(path: Path) -> bool:
    if not shutil.which("gnome-screenshot"):
        return False
    return _run_command(["gnome-screenshot", "-f", str(path)], path, timeout=25)


def _capture_with_scrot(path: Path) -> bool:
    if not shutil.which("scrot"):
        return False
    return _run_command(["scrot", str(path)], path)


def _capture_with_portal(path: Path, *, interactive: bool) -> bool:
    """xdg-desktop-portal screenshot via vql helper script when available."""
    try:
        from vql.adopt.portal_capture import capture_via_portal
    except ImportError:
        return False

    result = capture_via_portal(str(path), interactive=interactive)
    return bool(result.get("ok")) and path.is_file()


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
