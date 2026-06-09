# Web UI (`imgl serve`)

Port **8008** — tryb manualny i autonomiczny z podglądem i miniaturkami.

```bash
make install-dev
pip install -e ".[web,llm,capture]"
imgl capture -o screen.png --verify --analyze
imgl serve --port 8008 --image screen.png --llm --window region-bottom
```

## Panel

| Element | Funkcja |
|---------|---------|
| Zrzut ekranu | `POST /api/capture` — vdisplay mirror → analyze → VQL |
| Region (chips) | `region-top` / `region-bottom` |
| LLM katalog | Vision LLM na wycinku okna |
| Wykonuj na pulpicie | xdotool/ydotool (+ guard DISPLAY) |
| Zrzut po akcji | capture → analyze → VQL po każdym kroku |
| Karty akcji | Miniatura + klik |
| Agent | Cel → Start / Pętla |

Pliki sesji (przy domyślnej ścieżce obrazu): `layout.vql.json`, `layout.vql.imgl.json`, opcjonalnie `.capture.json` przy capture z CLI.

## REST API (web)

| Endpoint | Opis |
|----------|------|
| `GET /api/state` | Akcje, okna, historia, `vql_file` |
| `GET /api/annotated` | Mapa numerów |
| `POST /api/capture` | vdisplay capture + analyze |
| `POST /api/act` | `{index}` lub `{prompt}` |
| `POST /api/agent/run` | Pętla agenta |

Zobacz też [control-layer.md](control-layer.md) — port **8219** to osobne REST DSL (`rest2imgl`), nie mylić z web UI na 8008.

Pełny przykład: [examples/workflows/web-ui](../examples/workflows/web-ui/README.md).
