"""Optional dependency installers (imgl install img2nl|vdisplay|vql|control)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root(name: str, env_key: str, default: str) -> Path:
    raw = os.environ.get(env_key, default).strip()
    path = Path(raw).expanduser()
    if not path.is_dir():
        raise FileNotFoundError(
            f"{name} not found at {path} — set {env_key}=/path/to/{name}"
        )
    return path


def vdisplay_available() -> bool:
    try:
        import vdisplay.capture.host  # noqa: F401

        return True
    except ImportError:
        return False


def _auto_install_vdisplay_enabled() -> bool:
    raw = os.environ.get("IMGL_AUTO_INSTALL_VDISPLAY", "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def ensure_vdisplay(*, quiet: bool = False) -> bool:
    """Install vdisplay from VDISPLAY_ROOT when missing (built into imgl capture)."""
    if vdisplay_available():
        return True
    if not _auto_install_vdisplay_enabled():
        return False
    try:
        install_vdisplay()
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        if not quiet:
            print(f"vdisplay auto-install failed: {exc}", file=sys.stderr)
        return False
    return vdisplay_available()


def _pip_install_editable(path: Path, *, extras: str = "") -> None:
    spec = f"{path}{extras}" if extras else str(path)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", spec],
        check=True,
    )


def install_img2nl() -> Path:
    """pip install -e img2nl[analyze] for capture autodiag."""
    root = _repo_root("img2nl", "IMG2NL_ROOT", "~/github/wronai/img2nl")
    try:
        _pip_install_editable(root, extras="[analyze]")
    except subprocess.CalledProcessError:
        _pip_install_editable(root)
    print(f"OK img2nl: {root}")
    print(f"Test: {sys.executable} -m imgl.cli doctor --image screen.png --format yaml")
    return root


def install_vdisplay() -> Path:
    """pip install -e vdisplay[pillow] for OS window discovery."""
    root = _repo_root("vdisplay", "VDISPLAY_ROOT", "~/github/wronai/vdisplay")
    try:
        _pip_install_editable(root, extras="[pillow]")
    except subprocess.CalledProcessError:
        _pip_install_editable(root)
    print(f"OK vdisplay: {root}")
    print(
        "Test: "
        f"{sys.executable} -c "
        "'from vdisplay.discovery import list_windows; print(len(list_windows(apps_only=True)))'"
    )
    return root


def install_vql() -> Path:
    """pip install -e vql for portal capture on GNOME/Wayland."""
    root = _repo_root("vql", "VQL_ROOT", "~/github/oqlos/vql")
    _pip_install_editable(root)
    print(f"OK vql: {root}")
    print(f"Test: {sys.executable} -m imgl.cli capture --interactive -o /tmp/screen.png")
    return root


def install_control() -> None:
    """pip install -e nlp2imgl/dsl2imgl/rest2imgl/cli2imgl."""
    pkg_root = Path(__file__).resolve().parents[1] / "packages"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-e",
            str(pkg_root / "dsl2imgl"),
            "-e",
            str(pkg_root / "nlp2imgl"),
            "-e",
            str(pkg_root / "rest2imgl"),
            "-e",
            str(pkg_root / "cli2imgl"),
        ],
        check=True,
    )
    print("OK control: dsl2imgl, nlp2imgl, rest2imgl, cli2imgl")


__all__ = [
    "ensure_vdisplay",
    "install_control",
    "install_img2nl",
    "install_vdisplay",
    "install_vql",
    "vdisplay_available",
]
