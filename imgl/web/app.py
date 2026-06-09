"""FastAPI application for imgl web control."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from imgl.web.agent import pick_agent_action
from imgl.web.session import SessionManager, WebSettings
from imgl.web.thumbs import crop_bbox_png, window_bbox_dict


class SettingsBody(BaseModel):
    lang: str | None = None
    use_llm: bool | None = None
    filter_noise: bool | None = None
    execute: bool | None = None
    capture_after_action: bool | None = None
    selected_window_id: str | None = None
    llm_model: str | None = None
    catalog_max_items: int | None = None


class WindowBody(BaseModel):
    window_id: str | int | None = None


class ActBody(BaseModel):
    index: int | None = None
    prompt: str | None = None
    execute: bool | None = None
    recapture: bool | None = None


class CaptureBody(BaseModel):
    interactive: bool = False


class AgentStartBody(BaseModel):
    goal: str
    max_steps: int = Field(default=10, ge=1, le=100)
    execute: bool | None = None


class AgentStepBody(BaseModel):
    execute: bool | None = None


def create_app(
    *,
    work_dir: str | Path | None = None,
    image_path: str | Path | None = None,
    settings: WebSettings | None = None,
    auto_select_window: bool = True,
) -> FastAPI:
    base_dir = Path(work_dir or Path.cwd() / ".imgl" / "web").expanduser().resolve()
    manager = SessionManager.create(
        work_dir=base_dir,
        image_path=image_path,
        settings=settings,
    )
    if auto_select_window:
        manager.auto_select_first_window()

    app = FastAPI(
        title="imgl web",
        version="0.7.1",
        description="Manual and autonomous GUI control from screenshots",
    )
    static_dir = Path(__file__).resolve().parent / "static"
    if static_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        page = static_dir / "index.html"
        if not page.is_file():
            raise HTTPException(status_code=404, detail="index.html missing")
        return HTMLResponse(page.read_text(encoding="utf-8"))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "imgl-web"}

    @app.get("/api/state")
    def get_state() -> dict[str, Any]:
        return manager.session.state_dict()

    @app.get("/api/screenshot")
    def get_screenshot() -> FileResponse:
        path = Path(manager.session.image_path)
        if not path.is_file():
            raise HTTPException(status_code=404, detail="screenshot not found")
        return FileResponse(path, media_type="image/png")

    @app.get("/api/annotated")
    def get_annotated() -> Response:
        data = manager.session.annotated_png
        if not data:
            path = Path(manager.session.image_path)
            if path.is_file():
                return FileResponse(path, media_type="image/png")
            raise HTTPException(status_code=404, detail="annotated image unavailable")
        return Response(content=data, media_type="image/png")

    @app.get("/api/actions/{index}/thumb")
    def get_action_thumb(index: int) -> Response:
        option = next((opt for opt in manager.session.catalog if opt.index == index), None)
        if option is None:
            raise HTTPException(status_code=404, detail=f"action {index} not found")
        try:
            png = crop_bbox_png(manager.session.image_path, option.bbox)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return Response(content=png, media_type="image/png")

    @app.get("/api/windows/{index}/crop")
    def get_window_crop(index: int) -> Response:
        summary = next(
            (item for item in manager.session.window_summaries if item.index == index),
            None,
        )
        if summary is None:
            raise HTTPException(status_code=404, detail=f"window {index} not found")
        try:
            png = crop_bbox_png(
                manager.session.image_path,
                window_bbox_dict(summary.window),
                max_dim=480,
                padding=0,
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return Response(content=png, media_type="image/png")

    @app.post("/api/settings")
    def update_settings(body: SettingsBody) -> dict[str, Any]:
        s = manager.session.settings
        for key, value in body.model_dump(exclude_none=True).items():
            setattr(s, key, value)
        manager.session.refresh_catalog()
        return manager.session.state_dict()

    @app.post("/api/capture")
    def post_capture(body: CaptureBody) -> dict[str, Any]:
        try:
            manager.session.capture(interactive=body.interactive)
            manager.session.last_error = None
            return {"ok": True, "state": manager.session.state_dict()}
        except Exception as exc:
            manager.session.last_error = str(exc)
            return {
                "ok": False,
                "error": str(exc),
                "state": manager.session.state_dict(),
            }

    @app.post("/api/analyze")
    def post_analyze() -> dict[str, Any]:
        if not Path(manager.session.image_path).is_file():
            raise HTTPException(status_code=400, detail="no screenshot; capture first")
        manager.session.analyze(refresh=True)
        return manager.session.state_dict()

    @app.post("/api/window")
    def post_window(body: WindowBody) -> dict[str, Any]:
        if not manager.session.select_window(body.window_id):
            raise HTTPException(status_code=404, detail=f"window not found: {body.window_id}")
        return manager.session.state_dict()

    @app.post("/api/act")
    def post_act(body: ActBody) -> dict[str, Any]:
        if body.index is None and not body.prompt:
            raise HTTPException(status_code=400, detail="index or prompt required")
        record = manager.session.act(
            index=body.index,
            prompt=body.prompt,
            execute=body.execute,
            mode="manual",
            recapture=body.recapture,
        )
        return {"step": record.to_dict(), "state": manager.session.state_dict()}

    @app.post("/api/agent/start")
    def agent_start(body: AgentStartBody) -> dict[str, Any]:
        agent = manager.session.agent
        agent.running = True
        agent.finished = False
        agent.goal = body.goal.strip()
        agent.max_steps = body.max_steps
        agent.step_count = 0
        agent.last_reason = ""
        if body.execute is not None:
            manager.session.settings.execute = body.execute
        return manager.session.state_dict()

    @app.post("/api/agent/stop")
    def agent_stop() -> dict[str, Any]:
        manager.session.agent.running = False
        manager.session.agent.finished = True
        return manager.session.state_dict()

    @app.get("/api/agent/status")
    def agent_status() -> dict[str, Any]:
        return manager.session.agent.to_dict()

    @app.post("/api/agent/step")
    def agent_step(body: AgentStepBody) -> dict[str, Any]:
        agent = manager.session.agent
        if not agent.running:
            raise HTTPException(status_code=400, detail="agent not running; POST /api/agent/start")

        if agent.step_count >= agent.max_steps:
            agent.running = False
            agent.finished = True
            agent.last_reason = "max steps reached"
            return {
                "decision": {"status": "done", "reason": agent.last_reason},
                "step": None,
                "state": manager.session.state_dict(),
            }

        decision = pick_agent_action(
            agent.goal,
            manager.session.catalog,
            [step.to_dict() for step in manager.session.history],
            model=manager.session.settings.llm_model,
        )
        agent.last_reason = str(decision.get("reason") or decision.get("error") or "")

        if not decision.get("ok") or decision.get("status") == "done":
            agent.running = False
            agent.finished = True
            return {
                "decision": decision,
                "step": None,
                "state": manager.session.state_dict(),
            }

        record = manager.session.act(
            index=decision.get("index"),
            prompt=decision.get("prompt"),
            execute=body.execute,
            mode="agent",
        )
        agent.step_count += 1

        if not record.ok:
            agent.running = False
            agent.finished = True

        return {
            "decision": decision,
            "step": record.to_dict(),
            "state": manager.session.state_dict(),
        }

    @app.post("/api/agent/run")
    def agent_run(body: AgentStartBody) -> dict[str, Any]:
        """Run up to max_steps autonomously in one request."""
        start = agent_start(body)
        steps: list[dict[str, Any]] = []
        while manager.session.agent.running and manager.session.agent.step_count < body.max_steps:
            payload = agent_step(AgentStepBody(execute=body.execute))
            if payload.get("step"):
                steps.append(payload["step"])
            if payload.get("decision", {}).get("status") == "done":
                break
            if not manager.session.agent.running:
                break
        return {
            "steps": steps,
            "agent": manager.session.agent.to_dict(),
            "state": manager.session.state_dict(),
        }

    app.state.manager = manager
    return app


app = create_app()
