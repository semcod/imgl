"""DSL control bus for imgl."""

from dsl2imgl.bus import COMMAND_VERBS, QUERY_VERBS, dispatch, execute_dsl_line
from dsl2imgl.result import DslResult

__all__ = ["COMMAND_VERBS", "QUERY_VERBS", "dispatch", "execute_dsl_line", "DslResult"]
