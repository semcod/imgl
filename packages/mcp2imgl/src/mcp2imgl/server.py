"""MCP stdio server — thin wrappers over dsl2imgl."""

from __future__ import annotations

import json

from dsl2imgl import dispatch
from nlp2imgl.to_dsl import apply_nl, to_dsl


def run_stdio() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise SystemExit("pip install mcp2imgl[mcp]") from exc

    mcp = FastMCP("mcp2imgl")

    @mcp.tool()
    def imgl_run_command(command: str) -> str:
        """Run one imgl DSL line."""
        return dispatch(command).to_json()

    @mcp.tool()
    def imgl_to_dsl(prompt: str, image: str = "screen.png", window: str = "") -> str:
        """Convert NL to DSL without executing."""
        return to_dsl(prompt, image=image, window=window or None)

    @mcp.tool()
    def imgl_apply_nl(prompt: str, image: str = "screen.png", window: str = "", execute: bool = True) -> str:
        """NL → DSL → dispatch."""
        result = apply_nl(prompt, image=image, window=window or None, execute=execute)
        return json.dumps(result.to_dict(), ensure_ascii=False)

    mcp.run()
