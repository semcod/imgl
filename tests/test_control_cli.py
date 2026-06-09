"""Tests for imgl control CLI module."""

from __future__ import annotations

from pathlib import Path

import pytest

from imgl.control import default_image_path, default_window, run_doctor, run_execute


def test_default_image_path_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("IMGL_IMAGE", "/tmp/custom.png")
    assert default_image_path() == Path("/tmp/custom.png")


def test_default_window_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMGL_WINDOW", "region-top")
    assert default_window() == "region-top"


def test_run_doctor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    image = tmp_path / "screen.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)

    def fake_diag(_path, **_kwargs):
        return {"ok": True, "verdict": "real_ui", "is_fresh": True, "summary": "ok"}

    monkeypatch.setattr("imgl.control.diagnose_capture", fake_diag)
    text, code = run_doctor(image, output_format="yaml")
    assert code == 0
    assert "real_ui" in text or "verdict" in text


def test_run_execute_missing_image(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    nlp2imgl = pytest.importorskip("nlp2imgl.control")
    monkeypatch.setattr(nlp2imgl, "apply_nl_with_diag", lambda *_a, **_k: {"ok": True})
    missing = tmp_path / "nope.png"
    with pytest.raises(FileNotFoundError):
        run_execute("wpisz test", image=missing)


def test_run_execute_loads_openrouter_key_from_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    nlp2imgl = pytest.importorskip("nlp2imgl.control")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text('OPENROUTER_API_KEY="sk-from-dotenv"\n', encoding="utf-8")

    image = tmp_path / "screen.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 200)
    calls: list[dict] = []

    def fake_apply(*_a, **kwargs):
        calls.append(kwargs)
        return {"ok": True, "command": "TYPE test"}

    monkeypatch.setattr(nlp2imgl, "apply_nl_with_diag", fake_apply)
    _text, code = run_execute(
        "wpisz test w Chat input",
        image=image,
        use_llm=True,
        with_diagnostics=False,
        output_format="json",
    )
    assert code == 0
    assert calls and calls[0].get("use_llm") is True


def test_cli_doctor_help() -> None:
    from imgl.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["doctor", "--full", "--yaml"])
    assert args.command == "doctor"
    assert args.full is True
    assert args.yaml is True


def test_cli_execute_help() -> None:
    from imgl.cli import build_parser

    parser = build_parser()
    args = parser.parse_args(["execute", "wpisz x", "--dry-run", "--llm"])
    assert args.command == "execute"
    assert args.llm is True
    assert args.dry_run is True
    assert args.json is False
    assert args.yaml is False


def test_require_nlp2imgl_auto_installs_from_local_packages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import builtins
    import types

    from imgl import control as control_mod

    install_calls: list[str] = []
    import_calls = 0

    real_import = builtins.__import__

    def fake_apply_nl_with_diag(*_args, **_kwargs):
        return None

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        nonlocal import_calls
        if name == "nlp2imgl.control" or (
            fromlist and "nlp2imgl.control" in ".".join(fromlist)
        ):
            import_calls += 1
            if import_calls == 1:
                raise ImportError("no nlp2imgl")
            mod = types.ModuleType("nlp2imgl.control")
            mod.apply_nl_with_diag = fake_apply_nl_with_diag
            return mod
        return real_import(name, globals, locals, fromlist, level)

    def fake_install() -> None:
        install_calls.append("install")

    monkeypatch.setattr(builtins, "__import__", fake_import)
    monkeypatch.setattr(control_mod, "_control_packages_present", lambda: True)
    monkeypatch.setattr("imgl.installs.install_control", fake_install)

    fn = control_mod._require_nlp2imgl()
    assert install_calls == ["install"]
    assert fn is fake_apply_nl_with_diag


def test_cli_default_output_is_markdown() -> None:
    from imgl.autodiag import resolve_cli_output_format
    from imgl.cli import _output_format, build_parser

    assert resolve_cli_output_format() == "markdown"
    args = build_parser().parse_args(["execute", "wpisz x"])
    assert _output_format(args) == "markdown"
    args_json = build_parser().parse_args(["execute", "wpisz x", "--json"])
    assert _output_format(args_json) == "json"
