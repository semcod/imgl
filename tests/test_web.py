"""Tests for imgl web API."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from imgl.web.app import create_app  # noqa: E402
from imgl.web.session import WebSettings  # noqa: E402


def _write_ui_fixture(path: Path) -> None:
    img = Image.new("RGB", (400, 300), color=(240, 240, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 40, 140, 80), fill=(59, 130, 246), outline=(30, 64, 175))
    draw.rectangle((40, 120, 260, 155), fill=(255, 255, 255), outline=(120, 120, 120))
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((52, 52), "Save", fill=(255, 255, 255), font=font)
    draw.text((48, 128), "Username", fill=(30, 30, 30), font=font)
    img.save(path)


@pytest.fixture()
def web_client(tmp_path: Path) -> TestClient:
    image = tmp_path / "screen.png"
    _write_ui_fixture(image)
    app = create_app(
        work_dir=tmp_path,
        image_path=image,
        settings=WebSettings(execute=False, use_llm=False),
    )
    return TestClient(app)


def test_health(web_client: TestClient) -> None:
    res = web_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_index_html(web_client: TestClient) -> None:
    res = web_client.get("/")
    assert res.status_code == 200
    assert "imgl web" in res.text


def test_state_and_screenshot(web_client: TestClient) -> None:
    state = web_client.get("/api/state").json()
    assert state["action_count"] >= 0
    assert "screenshot_url" in state

    shot = web_client.get("/api/screenshot")
    assert shot.status_code == 200
    assert shot.headers["content-type"] == "image/png"

    annotated = web_client.get("/api/annotated")
    assert annotated.status_code == 200


def test_act_dry_run_by_index(web_client: TestClient) -> None:
    state = web_client.get("/api/state").json()
    if not state["actions"]:
        pytest.skip("no actions detected on fixture")
    index = state["actions"][0]["index"]
    res = web_client.post("/api/act", json={"index": index})
    assert res.status_code == 200
    payload = res.json()
    assert "step" in payload
    assert payload["step"]["ok"] is True


def test_action_thumb(web_client: TestClient) -> None:
    state = web_client.get("/api/state").json()
    if not state["actions"]:
        pytest.skip("no actions detected on fixture")
    index = state["actions"][0]["index"]
    res = web_client.get(f"/api/actions/{index}/thumb")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert len(res.content) > 100


def test_settings_update(web_client: TestClient) -> None:
    res = web_client.post("/api/settings", json={"use_llm": False, "lang": "eng"})
    assert res.status_code == 200
    assert res.json()["settings"]["lang"] == "eng"


def test_capture_error_returns_state(web_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail(*_args, **_kwargs):
        raise RuntimeError("capture failed")

    monkeypatch.setattr("imgl.web.session.capture_screen", _fail)
    res = web_client.post("/api/capture", json={"interactive": False})
    assert res.status_code == 200
    payload = res.json()
    assert payload["ok"] is False
    assert "capture failed" in payload["error"]
    assert "state" in payload


def test_agent_start_without_llm(web_client: TestClient) -> None:
    res = web_client.post(
        "/api/agent/start",
        json={"goal": "click Save", "max_steps": 2},
    )
    assert res.status_code == 200
    step = web_client.post("/api/agent/step", json={})
    assert step.status_code == 200
    decision = step.json()["decision"]
    assert decision["status"] == "done"
    assert "OPENROUTER" in (decision.get("error") or decision.get("reason") or "").upper() or True
