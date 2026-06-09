"""Stateful web session: capture → analyze → catalog → act loop."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any

from imgl.catalog import InteractiveOption, build_interactive_catalog
from imgl.capture import capture_screen
from imgl.config import ImglConfig
from imgl.execute import ExecuteResult, execute_action
from imgl.export import default_annotated_path, scene_to_annotated_image, write_vql_program
from imgl.interact import resolve_imgl_uri
from imgl.nlp2uri import ResolvedImglUri, prompt_to_imgl_uri
from imgl.scene_cache import load_or_analyze, save_scene_cache
from imgl.window_scope import (
    WindowSummary,
    apply_discovered_windows,
    discover_windows,
    get_discovered_window,
    summarize_windows,
)


@dataclass
class StepRecord:
    step_id: str
    timestamp: float
    mode: str
    prompt: str | None
    action_index: int | None
    uri: str | None
    action: dict[str, Any] | None
    execute: ExecuteResult | None
    image_path: str
    ok: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "mode": self.mode,
            "prompt": self.prompt,
            "action_index": self.action_index,
            "uri": self.uri,
            "action": self.action,
            "execute": self.execute.to_dict() if self.execute else None,
            "image_path": self.image_path,
            "ok": self.ok,
            "message": self.message,
        }


@dataclass
class AgentState:
    running: bool = False
    goal: str = ""
    max_steps: int = 10
    step_count: int = 0
    last_reason: str = ""
    finished: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "goal": self.goal,
            "max_steps": self.max_steps,
            "step_count": self.step_count,
            "last_reason": self.last_reason,
            "finished": self.finished,
        }


@dataclass
class WebSettings:
    lang: str = "eng+pol"
    use_llm: bool = False
    filter_noise: bool = True
    execute: bool = False
    capture_after_action: bool = True
    post_action_delay_s: float = 0.35
    llm_model: str = "openrouter/google/gemini-2.5-flash"
    catalog_max_items: int = 40
    selected_window_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "lang": self.lang,
            "use_llm": self.use_llm,
            "filter_noise": self.filter_noise,
            "execute": self.execute,
            "capture_after_action": self.capture_after_action,
            "post_action_delay_s": self.post_action_delay_s,
            "llm_model": self.llm_model,
            "catalog_max_items": self.catalog_max_items,
            "selected_window_id": self.selected_window_id,
        }


@dataclass
class WebSession:
    work_dir: Path
    image_path: str
    vql_file: str
    settings: WebSettings = field(default_factory=WebSettings)
    config: ImglConfig = field(default_factory=ImglConfig)
    scene: Any = None
    catalog: list[InteractiveOption] = field(default_factory=list)
    window_summaries: list[WindowSummary] = field(default_factory=list)
    history: list[StepRecord] = field(default_factory=list)
    agent: AgentState = field(default_factory=AgentState)
    annotated_png: bytes | None = None
    last_error: str | None = None

    def __post_init__(self) -> None:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.vql_file = str(Path(self.vql_file).resolve())
        self.image_path = str(Path(self.image_path).resolve())

    def refresh_catalog(self) -> None:
        if self.scene is None:
            return
        self.catalog = build_interactive_catalog(
            self.scene,
            image_path=self.image_path,
            vql_file=self.vql_file,
            lang=self.settings.lang,
            filter_noise=self.settings.filter_noise,
            use_llm=self.settings.use_llm,
            llm_model=self.settings.llm_model,
            max_items=self.settings.catalog_max_items,
            window_id=self.settings.selected_window_id,
            include_window_entries=self.settings.selected_window_id is None,
        )
        self._refresh_annotated_png()

    def analyze(self, *, refresh: bool = False) -> None:
        cfg = self.config
        cfg.lang = self.settings.lang
        cfg.use_llm_catalog = self.settings.use_llm
        cfg.llm_vision_model = self.settings.llm_model
        cfg.catalog_max_items = self.settings.catalog_max_items

        scene = load_or_analyze(
            self.image_path,
            vql_file=self.vql_file,
            lang=self.settings.lang,
            config=cfg,
            refresh=refresh,
        )
        scene = apply_discovered_windows(scene)
        write_vql_program(scene, self.vql_file)
        save_scene_cache(scene, self.vql_file)
        self.scene = scene
        self.window_summaries = summarize_windows(scene, image_path=self.image_path)
        self.refresh_catalog()
        self.last_error = None

    def capture(self, *, interactive: bool = False) -> str:
        out = self.work_dir / "screen.png"
        path = capture_screen(out, interactive=interactive)
        self.image_path = str(path.resolve())
        self.analyze(refresh=True)
        return self.image_path

    def select_window(self, window_ref: str | int | None) -> bool:
        if window_ref in {None, "", "all", "wszystkie"}:
            self.settings.selected_window_id = None
            self.refresh_catalog()
            return True
        if self.scene is None:
            return False
        window = get_discovered_window(self.scene, window_ref)
        if window is None:
            return False
        self.settings.selected_window_id = window.id
        self.refresh_catalog()
        return True

    def resolve_prompt(self, prompt: str) -> tuple[ResolvedImglUri | None, dict[str, Any] | None]:
        resolved = prompt_to_imgl_uri(
            prompt,
            image=self.image_path,
            file=self.vql_file,
            lang=self.settings.lang,
            catalog=self.catalog,
        )
        if resolved is None:
            return None, {"ok": False, "error": "Nie rozumiem polecenia"}
        result = resolve_imgl_uri(resolved.uri, self._interact_session())
        return resolved, result

    def resolve_index(self, index: int) -> tuple[ResolvedImglUri | None, dict[str, Any] | None]:
        return self.resolve_prompt(str(index))

    def act(
        self,
        *,
        prompt: str | None = None,
        index: int | None = None,
        execute: bool | None = None,
        mode: str = "manual",
        recapture: bool | None = None,
    ) -> StepRecord:
        do_execute = self.settings.execute if execute is None else execute
        should_recapture = (
            self.settings.capture_after_action if recapture is None else recapture
        )

        resolved: ResolvedImglUri | None = None
        result: dict[str, Any] | None = None
        if index is not None:
            resolved, result = self.resolve_index(index)
        elif prompt:
            resolved, result = self.resolve_prompt(prompt)
        else:
            record = self._step_record(
                mode=mode,
                prompt=prompt,
                action_index=index,
                uri=None,
                action=None,
                execute=None,
                ok=False,
                message="Brak index lub prompt",
            )
            self.history.append(record)
            return record

        if resolved is None or result is None:
            record = self._step_record(
                mode=mode,
                prompt=prompt,
                action_index=index,
                uri=None,
                action=None,
                execute=None,
                ok=False,
                message=(result or {}).get("error", "Nie rozpoznano akcji"),
            )
            self.history.append(record)
            return record

        if result.get("action") in {"list", "annotate", "analyze", "quit"}:
            if result.get("action") == "list":
                self.refresh_catalog()
            elif result.get("action") == "analyze":
                self.analyze(refresh=True)
            record = self._step_record(
                mode=mode,
                prompt=prompt or (str(index) if index is not None else None),
                action_index=index or resolved.option_index,
                uri=resolved.uri,
                action=result,
                execute=None,
                ok=bool(result.get("ok")),
                message=str(result.get("action")),
            )
            self.history.append(record)
            return record

        if not result.get("ok"):
            record = self._step_record(
                mode=mode,
                prompt=prompt or (str(index) if index is not None else None),
                action_index=index or resolved.option_index,
                uri=resolved.uri,
                action=None,
                execute=None,
                ok=False,
                message=str(result.get("error", "unknown")),
            )
            self.history.append(record)
            return record

        action_payload = {k: v for k, v in result.items() if k not in {"ok", "uri_action"}}
        exec_result: ExecuteResult | None = None
        message = "dry-run"
        if action_payload.get("action") in {"click", "type"}:
            exec_result = execute_action(action_payload, dry_run=not do_execute)
            message = exec_result.message
            if do_execute and exec_result.ok and should_recapture:
                time.sleep(self.settings.post_action_delay_s)
                try:
                    self.capture(interactive=False)
                    message = f"{exec_result.message}; odświeżono zrzut"
                except Exception as exc:
                    message = f"{exec_result.message}; capture failed: {exc}"
                    self.last_error = str(exc)

        record = self._step_record(
            mode=mode,
            prompt=prompt or (str(index) if index is not None else None),
            action_index=index or resolved.option_index,
            uri=resolved.uri,
            action=action_payload,
            execute=exec_result,
            ok=exec_result.ok if exec_result else True,
            message=message,
        )
        self.history.append(record)
        return record

    def state_dict(self) -> dict[str, Any]:
        windows = []
        for item in self.window_summaries:
            windows.append(
                {
                    "index": item.index,
                    "id": item.window.id,
                    "title": item.label,
                    "bbox": {
                        "x": item.bbox.x,
                        "y": item.bbox.y,
                        "w": item.bbox.w,
                        "h": item.bbox.h,
                    },
                    "interactive_count": item.interactive_count,
                    "element_count": item.element_count,
                    "crop_url": f"/api/windows/{item.index}/crop",
                }
            )
        actions = []
        for opt in self.catalog:
            entry = opt.to_dict()
            entry["thumb_url"] = f"/api/actions/{opt.index}/thumb"
            actions.append(entry)
        return {
            "image_path": self.image_path,
            "vql_file": self.vql_file,
            "screenshot_url": "/api/screenshot",
            "annotated_url": "/api/annotated",
            "scene_size": {
                "width": self.scene.width if self.scene else 0,
                "height": self.scene.height if self.scene else 0,
            },
            "settings": self.settings.to_dict(),
            "windows": windows,
            "actions": actions,
            "action_count": len(self.catalog),
            "history": [step.to_dict() for step in self.history[-30:]],
            "agent": self.agent.to_dict(),
            "last_error": self.last_error,
        }

    def _refresh_annotated_png(self) -> None:
        if self.scene is None:
            self.annotated_png = None
            return
        window = (
            get_discovered_window(self.scene, self.settings.selected_window_id)
            if self.settings.selected_window_id
            else None
        )
        image = scene_to_annotated_image(
            self.scene,
            self.catalog,
            source_image=self.image_path,
            window=window,
        )
        buf = BytesIO()
        image.convert("RGB").save(buf, format="PNG", optimize=True)
        self.annotated_png = buf.getvalue()

    def _interact_session(self) -> Any:
        from imgl.interact import InteractSession

        return InteractSession(
            image_path=self.image_path,
            vql_file=self.vql_file,
            lang=self.settings.lang,
            scene=self.scene,
            catalog=self.catalog,
            filter_noise=self.settings.filter_noise,
            use_llm=self.settings.use_llm,
            llm_model=self.settings.llm_model,
            catalog_max_items=self.settings.catalog_max_items,
            selected_window_id=self.settings.selected_window_id,
            window_summaries=self.window_summaries,
        )

    def _step_record(
        self,
        *,
        mode: str,
        prompt: str | None,
        action_index: int | None,
        uri: str | None,
        action: dict[str, Any] | None,
        execute: ExecuteResult | None,
        ok: bool,
        message: str,
    ) -> StepRecord:
        return StepRecord(
            step_id=str(uuid.uuid4()),
            timestamp=time.time(),
            mode=mode,
            prompt=prompt,
            action_index=action_index,
            uri=uri,
            action=action,
            execute=execute,
            image_path=self.image_path,
            ok=ok,
            message=message,
        )


class SessionManager:
    """Single global session for local desktop control."""

    def __init__(self, session: WebSession) -> None:
        self.session = session

    @classmethod
    def create(
        cls,
        *,
        work_dir: str | Path,
        image_path: str | Path | None = None,
        settings: WebSettings | None = None,
    ) -> SessionManager:
        work = Path(work_dir).expanduser().resolve()
        work.mkdir(parents=True, exist_ok=True)
        img = Path(image_path).expanduser().resolve() if image_path else work / "screen.png"
        if not img.is_file():
            img = work / "screen.png"
        session = WebSession(
            work_dir=work,
            image_path=str(img),
            vql_file=str(work / "layout.vql.json"),
            settings=settings or WebSettings(),
        )
        if Path(session.image_path).is_file():
            session.analyze(refresh=False)
            if settings and settings.selected_window_id:
                session.select_window(settings.selected_window_id)
        return cls(session)

    def auto_select_first_window(self) -> bool:
        """Pick first discovered region when screen has multiple windows."""
        if self.session.settings.selected_window_id:
            return True
        if len(self.session.window_summaries) <= 1:
            return False
        first = self.session.window_summaries[0]
        return self.session.select_window(first.window.id)
