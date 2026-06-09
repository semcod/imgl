"""Web UI and REST API for manual and autonomous screen control."""

__all__ = ["create_app"]


def create_app(*args, **kwargs):
    """Lazy import to avoid fastapi dependency when not needed."""
    from imgl.web.app import create_app as _create_app

    return _create_app(*args, **kwargs)
