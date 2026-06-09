"""Dict ↔ protobuf DslEnvelope / DslResult."""

from __future__ import annotations

import json
from typing import Any, Callable

from dsl2imgl.grammar import parse_line, to_text
from dsl2imgl.result import DslResult
from dsl2imgl.v1 import command_pb2, result_pb2

_BODY_MAP = {
    "HEALTH": "health",
    "CAPTURE": "capture",
    "ANALYZE": "analyze",
    "ACTIONS": "actions",
    "RESOLVE": "resolve",
    "CLICK": "click",
    "TYPE": "type",
    "KEY": "key",
    "EXECUTE": "execute",
    "AGENT": "agent",
}


def _assign_optional_str(msg: Any, field: str, cmd: dict[str, Any], key: str) -> None:
    if cmd.get(key):
        setattr(msg, field, str(cmd[key]))


def _assign_execute_flag(msg: Any, cmd: dict[str, Any]) -> None:
    msg.execute = bool(cmd.get("execute", True))


def _set_capture_body(msg: Any, cmd: dict[str, Any]) -> None:
    _assign_optional_str(msg, "out", cmd, "out")
    msg.interactive = bool(cmd.get("interactive"))


def _set_analyze_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.image = str(cmd.get("image", "screen.png"))
    _assign_optional_str(msg, "file", cmd, "file")
    _assign_optional_str(msg, "window", cmd, "window")
    msg.llm = bool(cmd.get("llm"))


def _set_actions_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.image = str(cmd.get("image", "screen.png"))
    _assign_optional_str(msg, "window", cmd, "window")
    msg.llm = bool(cmd.get("llm"))


def _set_resolve_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.prompt = str(cmd.get("prompt", ""))
    _assign_optional_str(msg, "image", cmd, "image")
    _assign_optional_str(msg, "window", cmd, "window")


def _set_click_body(msg: Any, cmd: dict[str, Any]) -> None:
    if cmd.get("index") is not None:
        msg.index = int(cmd["index"])
    _assign_optional_str(msg, "prompt", cmd, "prompt")
    _assign_optional_str(msg, "image", cmd, "image")
    _assign_optional_str(msg, "window", cmd, "window")
    _assign_execute_flag(msg, cmd)


def _set_type_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.value = str(cmd.get("value", ""))
    _assign_optional_str(msg, "field", cmd, "field")
    _assign_optional_str(msg, "image", cmd, "image")
    _assign_optional_str(msg, "window", cmd, "window")
    _assign_execute_flag(msg, cmd)


def _set_key_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.keys = str(cmd.get("keys", "Return"))
    _assign_optional_str(msg, "image", cmd, "image")
    _assign_optional_str(msg, "window", cmd, "window")
    _assign_execute_flag(msg, cmd)


def _set_execute_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.prompt = str(cmd.get("prompt", ""))
    _assign_optional_str(msg, "image", cmd, "image")
    _assign_optional_str(msg, "window", cmd, "window")
    _assign_execute_flag(msg, cmd)


def _set_agent_body(msg: Any, cmd: dict[str, Any]) -> None:
    msg.goal = str(cmd.get("goal", ""))
    if cmd.get("max_steps") is not None:
        msg.max_steps = int(cmd["max_steps"])
    _assign_optional_str(msg, "image", cmd, "image")
    _assign_optional_str(msg, "window", cmd, "window")


_SET_BODY_HANDLERS: dict[str, Callable[[Any, dict[str, Any]], None]] = {
    "CAPTURE": _set_capture_body,
    "ANALYZE": _set_analyze_body,
    "ACTIONS": _set_actions_body,
    "RESOLVE": _set_resolve_body,
    "CLICK": _set_click_body,
    "TYPE": _set_type_body,
    "KEY": _set_key_body,
    "EXECUTE": _set_execute_body,
    "AGENT": _set_agent_body,
}


def _set_body(envelope: command_pb2.DslEnvelope, cmd: dict[str, Any]) -> None:
    verb = str(cmd.get("verb", "")).upper()
    handler = _SET_BODY_HANDLERS.get(verb)
    if not handler:
        return
    handler(getattr(envelope, _BODY_MAP[verb]), cmd)


def _dict_optional_str(cmd: dict[str, Any], msg: Any, key: str) -> None:
    value = getattr(msg, key, None)
    if value:
        cmd[key] = value


def _dict_execute_flag(cmd: dict[str, Any], msg: Any) -> None:
    if not msg.execute:
        cmd["execute"] = False


def _dict_capture_body(cmd: dict[str, Any], msg: Any) -> None:
    _dict_optional_str(cmd, msg, "out")
    if msg.interactive:
        cmd["interactive"] = True


def _dict_analyze_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["image"] = msg.image or "screen.png"
    _dict_optional_str(cmd, msg, "file")
    _dict_optional_str(cmd, msg, "window")
    if msg.llm:
        cmd["llm"] = True


def _dict_actions_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["image"] = msg.image or "screen.png"
    _dict_optional_str(cmd, msg, "window")
    if msg.llm:
        cmd["llm"] = True


def _dict_resolve_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["prompt"] = msg.prompt
    _dict_optional_str(cmd, msg, "image")
    _dict_optional_str(cmd, msg, "window")


def _dict_click_body(cmd: dict[str, Any], msg: Any) -> None:
    if msg.index:
        cmd["index"] = int(msg.index)
    _dict_optional_str(cmd, msg, "prompt")
    _dict_optional_str(cmd, msg, "image")
    _dict_optional_str(cmd, msg, "window")
    _dict_execute_flag(cmd, msg)


def _dict_type_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["value"] = msg.value
    _dict_optional_str(cmd, msg, "field")
    _dict_optional_str(cmd, msg, "image")
    _dict_optional_str(cmd, msg, "window")
    _dict_execute_flag(cmd, msg)


def _dict_key_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["keys"] = msg.keys or "Return"
    _dict_optional_str(cmd, msg, "image")
    _dict_optional_str(cmd, msg, "window")
    _dict_execute_flag(cmd, msg)


def _dict_execute_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["prompt"] = msg.prompt
    _dict_optional_str(cmd, msg, "image")
    _dict_optional_str(cmd, msg, "window")
    _dict_execute_flag(cmd, msg)


def _dict_agent_body(cmd: dict[str, Any], msg: Any) -> None:
    cmd["goal"] = msg.goal
    if msg.max_steps:
        cmd["max_steps"] = int(msg.max_steps)
    _dict_optional_str(cmd, msg, "image")
    _dict_optional_str(cmd, msg, "window")


_DICT_BODY_HANDLERS: dict[str, Callable[[dict[str, Any], Any], None]] = {
    "CAPTURE": _dict_capture_body,
    "ANALYZE": _dict_analyze_body,
    "ACTIONS": _dict_actions_body,
    "RESOLVE": _dict_resolve_body,
    "CLICK": _dict_click_body,
    "TYPE": _dict_type_body,
    "KEY": _dict_key_body,
    "EXECUTE": _dict_execute_body,
    "AGENT": _dict_agent_body,
}


def dict_to_envelope(cmd: dict[str, Any], *, default_file: str = "", correlation_id: str = "") -> command_pb2.DslEnvelope:
    envelope = command_pb2.DslEnvelope()
    envelope.verb = str(cmd.get("verb", "")).upper()
    _set_body(envelope, cmd)
    envelope.default_file = default_file
    envelope.correlation_id = correlation_id
    return envelope


def envelope_to_dict(envelope: command_pb2.DslEnvelope) -> dict[str, Any]:
    verb = envelope.verb.upper()
    cmd: dict[str, Any] = {"verb": verb}
    field = _BODY_MAP.get(verb)
    if not field or envelope.WhichOneof("body") != field:
        return cmd
    handler = _DICT_BODY_HANDLERS.get(verb)
    if handler:
        handler(cmd, getattr(envelope, field))
    return cmd


def encode_protobuf(cmd: dict[str, Any], *, default_file: str = "", correlation_id: str = "") -> bytes:
    return dict_to_envelope(cmd, default_file=default_file, correlation_id=correlation_id).SerializeToString()


def decode_protobuf(data: bytes) -> dict[str, Any]:
    envelope = command_pb2.DslEnvelope()
    envelope.ParseFromString(data)
    return envelope_to_dict(envelope)


def encode_text_to_protobuf(line: str, *, default_file: str = "", correlation_id: str = "") -> bytes:
    payload = parse_line(line)
    if not payload:
        raise ValueError("empty command")
    return encode_protobuf(payload, default_file=default_file, correlation_id=correlation_id)


def decode_protobuf_to_text(data: bytes) -> str:
    return to_text(decode_protobuf(data))


def result_to_pb(result: DslResult) -> result_pb2.DslResult:
    pb = result_pb2.DslResult()
    pb.ok = result.ok
    pb.verb = result.verb
    pb.command = result.command
    pb.action = result.action
    pb.output = result.output
    pb.data_json = json.dumps(result.data, ensure_ascii=False).encode("utf-8")
    pb.error = result.error or ""
    pb.event_id = result.event_id or ""
    return pb


def pb_to_result(pb: result_pb2.DslResult) -> DslResult:
    data: dict[str, Any] = {}
    if pb.data_json:
        try:
            data = json.loads(pb.data_json.decode("utf-8"))
        except json.JSONDecodeError:
            data = {}
    return DslResult(
        ok=pb.ok,
        verb=pb.verb,
        command=pb.command,
        action=pb.action,
        output=pb.output,
        data=data,
        error=pb.error or "",
        event_id=pb.event_id or "",
    )


def encode_result_protobuf(result: DslResult) -> bytes:
    return result_to_pb(result).SerializeToString()
