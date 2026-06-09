"""Regression tests for nlp2imgl CLI split (STARTER-004)."""

from __future__ import annotations

import argparse

import pytest

nlp2imgl_cli = pytest.importorskip("nlp2imgl.cli")
nlp2imgl_cli_commands = pytest.importorskip("nlp2imgl.cli_commands")
nlp2imgl_cli_parser = pytest.importorskip("nlp2imgl.cli_parser")


def test_build_parser_registers_subcommands() -> None:
    parser = nlp2imgl_cli_parser.build_parser()
    args = parser.parse_args(["to-dsl", "kliknij Save"])
    assert args.cmd == "to-dsl"
    assert args.prompt == "kliknij Save"

    args = parser.parse_args(["apply", "wpisz hello", "--dry-run", "--json"])
    assert args.cmd == "apply"
    assert args.dry_run is True
    assert args.json is True

    args = parser.parse_args(["doctor", "--full", "--yaml"])
    assert args.cmd == "doctor"
    assert args.full is True
    assert args.yaml is True


def test_run_to_dsl_prints_line(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "nlp2imgl.cli_commands.to_dsl",
        lambda prompt, **kwargs: f"EXECUTE {prompt!r}",
    )
    args = argparse.Namespace(prompt="kliknij Save", image="screen.png", window=None)
    code = nlp2imgl_cli_commands.run_to_dsl(args)
    assert code == 0
    assert "kliknij Save" in capsys.readouterr().out


def test_run_apply_uses_json_when_requested(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = {"ok": True, "verb": "EXECUTE"}
    monkeypatch.setattr(
        "nlp2imgl.cli_commands.apply_nl_with_diag",
        lambda *_a, **_k: payload,
    )
    args = argparse.Namespace(
        prompt="wpisz test",
        image="screen.png",
        window=None,
        dry_run=True,
        no_diagnose=True,
        llm=False,
        json=True,
        yaml=False,
    )
    code = nlp2imgl_cli_commands.run_apply(args)
    assert code == 0
    assert '"ok": true' in capsys.readouterr().out.lower()


def test_run_doctor_exits_nonzero_on_stale_capture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "nlp2imgl.cli_commands.doctor_capture",
        lambda *_a, **_k: {"verdict": "stale_capture", "is_fresh": False},
    )
    monkeypatch.setattr(
        "nlp2imgl.cli_commands.print_report",
        lambda *_a, **_k: None,
    )
    args = argparse.Namespace(
        image=None,
        window=None,
        full=False,
        locale="pl",
        json=False,
        yaml=False,
    )
    assert nlp2imgl_cli_commands.run_doctor(args) == 1


def test_main_dispatches_apply(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        nlp2imgl_cli,
        "_COMMAND_HANDLERS",
        {"apply": lambda _args: 42},
    )
    assert nlp2imgl_cli.main(["apply", "wpisz test", "--dry-run"]) == 42
