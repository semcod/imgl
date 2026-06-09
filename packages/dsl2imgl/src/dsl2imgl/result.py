"""DSL result dataclass."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DslResult:
    ok: bool
    verb: str = ""
    command: str = ""
    action: str = ""
    output: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    error: str = ""
    event_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "verb": self.verb,
            "command": self.command,
            "action": self.action,
            "output": self.output,
            "data": self.data,
            "error": self.error,
            "event_id": self.event_id,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
