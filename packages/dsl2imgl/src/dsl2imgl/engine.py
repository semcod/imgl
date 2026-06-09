"""Backward-compatible shim — re-export bus entry points."""

from dsl2imgl.bus import dispatch, execute_dsl, execute_dsl_line

__all__ = ["dispatch", "execute_dsl", "execute_dsl_line"]
