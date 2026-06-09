"""Dict ↔ protobuf DslEnvelope / DslResult."""

from __future__ import annotations

import json
from typing import Any

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


def _set_body(envelope: command_pb2.DslEnvelope, cmd: dict[str, Any]) -> None:
    verb = str(cmd.get("verb", "")).upper()
    field = _BODY_MAP.get(verb)
    if not field:
        return
    msg = getattr(envelope, field)
    if verb == "CAPTURE":
        if cmd.get("out"):
            msg.out = str(cmd["out"])
        msg.interactive = bool(cmd.get("interactive"))
    elif verb == "ANALYZE":
        msg.image = str(cmd.get("image", "screen.png"))
        if cmd.get("file"):
            msg.file = str(cmd["file"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])
        msg.llm = bool(cmd.get("llm"))
    elif verb == "ACTIONS":
        msg.image = str(cmd.get("image", "screen.png"))
        if cmd.get("window"):
            msg.window = str(cmd["window"])
        msg.llm = bool(cmd.get("llm"))
    elif verb == "RESOLVE":
        msg.prompt = str(cmd.get("prompt", ""))
        if cmd.get("image"):
            msg.image = str(cmd["image"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])
    elif verb == "CLICK":
        if cmd.get("index") is not None:
            msg.index = int(cmd["index"])
        if cmd.get("prompt"):
            msg.prompt = str(cmd["prompt"])
        if cmd.get("image"):
            msg.image = str(cmd["image"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])
        msg.execute = bool(cmd.get("execute", True))
    elif verb == "TYPE":
        msg.value = str(cmd.get("value", ""))
        if cmd.get("field"):
            msg.field = str(cmd["field"])
        if cmd.get("image"):
            msg.image = str(cmd["image"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])
        msg.execute = bool(cmd.get("execute", True))
    elif verb == "KEY":
        msg.keys = str(cmd.get("keys", "Return"))
        if cmd.get("image"):
            msg.image = str(cmd["image"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])
        msg.execute = bool(cmd.get("execute", True))
    elif verb == "EXECUTE":
        msg.prompt = str(cmd.get("prompt", ""))
        if cmd.get("image"):
            msg.image = str(cmd["image"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])
        msg.execute = bool(cmd.get("execute", True))
    elif verb == "AGENT":
        msg.goal = str(cmd.get("goal", ""))
        if cmd.get("max_steps") is not None:
            msg.max_steps = int(cmd["max_steps"])
        if cmd.get("image"):
            msg.image = str(cmd["image"])
        if cmd.get("window"):
            msg.window = str(cmd["window"])


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
    msg = getattr(envelope, field)
    if verb == "CAPTURE":
        if msg.out:
            cmd["out"] = msg.out
        if msg.interactive:
            cmd["interactive"] = True
    elif verb == "ANALYZE":
        cmd["image"] = msg.image or "screen.png"
        if msg.file:
            cmd["file"] = msg.file
        if msg.window:
            cmd["window"] = msg.window
        if msg.llm:
            cmd["llm"] = True
    elif verb == "ACTIONS":
        cmd["image"] = msg.image or "screen.png"
        if msg.window:
            cmd["window"] = msg.window
        if msg.llm:
            cmd["llm"] = True
    elif verb == "RESOLVE":
        cmd["prompt"] = msg.prompt
        if msg.image:
            cmd["image"] = msg.image
        if msg.window:
            cmd["window"] = msg.window
    elif verb == "CLICK":
        if msg.index:
            cmd["index"] = int(msg.index)
        if msg.prompt:
            cmd["prompt"] = msg.prompt
        if msg.image:
            cmd["image"] = msg.image
        if msg.window:
            cmd["window"] = msg.window
        if not msg.execute:
            cmd["execute"] = False
    elif verb == "TYPE":
        cmd["value"] = msg.value
        if msg.field:
            cmd["field"] = msg.field
        if msg.image:
            cmd["image"] = msg.image
        if msg.window:
            cmd["window"] = msg.window
        if not msg.execute:
            cmd["execute"] = False
    elif verb == "KEY":
        cmd["keys"] = msg.keys or "Return"
        if msg.image:
            cmd["image"] = msg.image
        if msg.window:
            cmd["window"] = msg.window
        if not msg.execute:
            cmd["execute"] = False
    elif verb == "EXECUTE":
        cmd["prompt"] = msg.prompt
        if msg.image:
            cmd["image"] = msg.image
        if msg.window:
            cmd["window"] = msg.window
        if not msg.execute:
            cmd["execute"] = False
    elif verb == "AGENT":
        cmd["goal"] = msg.goal
        if msg.max_steps:
            cmd["max_steps"] = int(msg.max_steps)
        if msg.image:
            cmd["image"] = msg.image
        if msg.window:
            cmd["window"] = msg.window
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
