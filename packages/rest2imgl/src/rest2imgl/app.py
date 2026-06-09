"""FastAPI REST adapter for dsl2imgl."""

from __future__ import annotations

import json
from typing import Any

from dsl2imgl import dispatch
from dsl2imgl.codec import envelope_from_bytes
from dsl2imgl.pb_codec import encode_result_protobuf
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from nlp2imgl.to_dsl import apply_nl, to_dsl
from pydantic import BaseModel


class NlBody(BaseModel):
    prompt: str
    image: str = "screen.png"
    window: str | None = None
    execute: bool = True


def create_app() -> FastAPI:
    app = FastAPI(title="rest2imgl", version="0.1.0")

    @app.get("/")
    def root() -> dict[str, Any]:
        return {
            "service": "rest2imgl",
            "health": "/health",
            "dsl": "POST /v1/dsl",
            "nl": "POST /v1/nl",
            "web_ui": "imgl serve --port 8008",
        }

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rest2imgl"}

    @app.post("/v1/dsl")
    async def post_dsl(request: Request) -> Response:
        ct = request.headers.get("content-type", "text/plain").split(";")[0].strip()
        body = await request.body()
        if ct == "application/json":
            result = dispatch(json.loads(body.decode("utf-8")))
        elif ct == "application/x-protobuf":
            result = dispatch(body)
        else:
            result = dispatch(body.decode("utf-8").strip())
        if ct == "application/x-protobuf":
            return Response(content=encode_result_protobuf(result), media_type="application/x-protobuf")
        if ct == "text/plain":
            return PlainTextResponse(result.output or result.to_json())
        return JSONResponse(result.to_dict())

    @app.post("/v1/commands")
    async def post_commands(request: Request) -> Response:
        return await post_dsl(request)

    @app.post("/v1/nl")
    def post_nl(body: NlBody) -> JSONResponse:
        result = apply_nl(
            body.prompt,
            image=body.image,
            window=body.window,
            execute=body.execute,
        )
        return JSONResponse(
            {
                "dsl": to_dsl(body.prompt, image=body.image, window=body.window, execute=body.execute),
                "result": result.to_dict(),
            }
        )

    return app


app = create_app()
