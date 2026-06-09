"""Autonomous agent: LLM picks next catalog action toward a goal."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from imgl.catalog import InteractiveOption
from imgl.llm_catalog import _load_env_files, llm_available


_AGENT_SYSTEM = """You control a desktop GUI via numbered actions from a screenshot catalog.
Pick the single best next action to progress toward the user's goal.
Return strict JSON only:
{
  "status": "act" | "done",
  "index": <catalog number when status=act>,
  "type_text": "<text to type when action is input, else empty>",
  "reason": "<short explanation>"
}
Rules:
- Use only valid catalog indices.
- Prefer buttons/links for navigation; use type_text only for input fields.
- Return status=done when the goal appears achieved or no useful action exists.
- Max one action per response."""


def _catalog_lines(catalog: list[InteractiveOption]) -> str:
    lines = []
    for opt in catalog:
        label = opt.label or opt.text or opt.element_id
        lines.append(
            f"{opt.index}. [{opt.category}/{opt.element_type}] {label}"
            f" @ ({opt.position[0]},{opt.position[1]})"
        )
    return "\n".join(lines) or "(empty catalog)"


def _history_lines(history: list[dict[str, Any]], limit: int = 8) -> str:
    rows = []
    for step in history[-limit:]:
        rows.append(
            f"- {step.get('mode')}: {step.get('prompt') or step.get('action_index')} "
            f"→ {step.get('message')}"
        )
    return "\n".join(rows) or "(no history)"


def pick_agent_action(
    goal: str,
    catalog: list[InteractiveOption],
    history: list[dict[str, Any]],
    *,
    model: str | None = None,
) -> dict[str, Any]:
    """Return agent decision: {status, index?, type_text?, reason, ok, error?}."""
    if not goal.strip():
        return {"ok": False, "error": "goal is empty", "status": "done"}
    if not catalog:
        return {"ok": False, "error": "catalog is empty", "status": "done"}

    _load_env_files()
    if not llm_available():
        return {"ok": False, "error": "OPENROUTER_API_KEY not configured", "status": "done"}

    try:
        import litellm
    except ImportError:
        return {"ok": False, "error": "litellm not installed (pip install -e '.[llm]')", "status": "done"}

    os.environ.setdefault("LITELLM_LOG", "ERROR")
    chosen_model = model or os.getenv(
        "IMGL_AGENT_MODEL",
        "openrouter/google/gemini-2.5-flash",
    )
    user_prompt = (
        f"Goal: {goal.strip()}\n\n"
        f"Recent steps:\n{_history_lines(history)}\n\n"
        f"Catalog:\n{_catalog_lines(catalog)}\n"
    )
    try:
        response = litellm.completion(
            model=chosen_model,
            messages=[
                {"role": "system", "content": _AGENT_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        raw = response.choices[0].message.content or ""
    except Exception as exc:
        return {"ok": False, "error": str(exc), "status": "done"}

    parsed = _parse_agent_json(raw)
    if parsed is None:
        return {"ok": False, "error": f"invalid LLM JSON: {raw[:200]}", "status": "done", "raw": raw}

    status = str(parsed.get("status", "done")).lower()
    reason = str(parsed.get("reason", ""))
    if status == "done":
        return {"ok": True, "status": "done", "reason": reason, "raw": parsed}

    index = parsed.get("index")
    try:
        index_int = int(index)
    except (TypeError, ValueError):
        return {"ok": False, "error": f"invalid index: {index}", "status": "done", "raw": parsed}

    valid = {opt.index for opt in catalog}
    if index_int not in valid:
        return {
            "ok": False,
            "error": f"index {index_int} not in catalog",
            "status": "done",
            "raw": parsed,
        }

    option = next(opt for opt in catalog if opt.index == index_int)
    type_text = str(parsed.get("type_text") or "").strip()
    if option.category == "input" and type_text:
        prompt = f"wpisz {type_text} w {option.label or option.text or 'pole'}"
    else:
        prompt = str(index_int)

    return {
        "ok": True,
        "status": "act",
        "index": index_int,
        "prompt": prompt,
        "reason": reason,
        "raw": parsed,
    }


def _parse_agent_json(raw: str) -> dict[str, Any] | None:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
