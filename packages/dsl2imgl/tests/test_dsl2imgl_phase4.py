"""Phase 4 tests: JSON Schema, Protobuf, EventStore."""

from __future__ import annotations

from pathlib import Path

from dsl2imgl.codec import envelope_from_bytes, envelope_to_bytes, parse_text, roundtrip_text
from dsl2imgl.events import EventStore
from dsl2imgl.pb_codec import decode_protobuf_to_text, encode_text_to_protobuf
from dsl2imgl.schema_registry import all_verbs, validate_schemas
from dsl2imgl import dispatch


def test_schema_registry_covers_all_verbs() -> None:
    assert validate_schemas() == []
    verbs = all_verbs()
    assert "HEALTH" in verbs
    assert "CAPTURE" in verbs
    assert "TYPE" in verbs
    assert len(verbs) == 10


def test_parse_text_validates_health() -> None:
    payload = parse_text("HEALTH")
    assert payload["verb"] == "HEALTH"


def test_protobuf_roundtrip_type() -> None:
    line = 'TYPE "hello" IN "Chat input" IMAGE screen.png WINDOW region-bottom EXECUTE 0'
    wire = encode_text_to_protobuf(line)
    back = decode_protobuf_to_text(wire)
    assert "TYPE" in back
    assert "hello" in back
    payload = envelope_from_bytes(wire)
    assert payload["verb"] == "TYPE"
    assert payload["value"] == "hello"


def test_codec_roundtrip_text() -> None:
    line = "KEY ctrl+Return EXECUTE 0"
    assert "KEY" in roundtrip_text(line)


def test_dispatch_bytes_envelope() -> None:
    wire = envelope_to_bytes({"verb": "HEALTH"})
    result = dispatch(wire)
    assert result.ok
    assert result.verb == "HEALTH"


def test_event_store_append_command(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "dsl.events.pb", fmt="protobuf")
    event_id = store.append_command(
        {"verb": "KEY", "keys": "Return", "execute": False},
        {"ok": True, "verb": "KEY", "output": "dry"},
    )
    assert event_id
    events = store.replay_pb()
    assert len(events) == 1
    assert events[0].command["verb"] == "KEY"


def test_command_dispatch_records_event_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "dsl2imgl.bus.EventStore.for_default",
        lambda *_a, **_k: EventStore(tmp_path / "dsl.events.pb", fmt="protobuf"),
    )
    result = dispatch("KEY Return EXECUTE 0")
    assert result.ok
    assert result.event_id
