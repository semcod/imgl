"""Path resolution helpers."""

from __future__ import annotations

from pathlib import Path


def resolve_image_path(source: str | Path) -> Path:
    """Resolve and validate an image path."""
    path = Path(source).expanduser()
    if path.is_file():
        return path.resolve()

    candidates = [path]
    if not path.is_absolute():
        candidates.append(Path.cwd() / path)

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()

    cwd = Path.cwd()
    hint = (
        f"Image not found: {source}\n"
        f"  cwd: {cwd}\n"
        "Tips:\n"
        "  - use an absolute path to an existing PNG/JPEG\n"
        "  - capture first: imgl capture -o screen.png\n"
        "  - example fixture: tests/fixtures/large.png"
    )
    raise FileNotFoundError(hint)


def resolve_image_path_optional(source: str | Path | None) -> tuple[Path | None, str | None]:
    """Like resolve_image_path but returns (path, error) instead of raising."""
    if not source:
        return None, "image= query param required"
    try:
        return resolve_image_path(source), None
    except FileNotFoundError as exc:
        return None, str(exc)
