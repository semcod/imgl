# Web UI (`imgl serve`)

Port **8008** — tryb manualny i autonomiczny z podglądem i miniaturkami.

```bash
pip install -e ".[web,llm,capture]"
imgl serve --port 8008 --image screen.png --llm --window region-bottom
```

## Panel

| Element | Funkcja |
|---------|---------|
| Zrzut ekranu | `POST /api/capture` (portal Wayland) |
| Region (chips) | `region-top` / `region-bottom` |
| LLM katalog | Vision LLM na wycinku okna |
| Wykonuj na pulpicie | xdotool/ydotool |
| Zrzut po akcji | capture → analyze po każdym kroku |
| Karty akcji | Miniatura + klik |
| Agent | Cel → Start / Pętla |

## REST API (web)

| Endpoint | Opis |
|----------|------|
| `GET /api/state` | Akcje, okna, historia |
| `GET /api/annotated` | Mapa numerów |
| `POST /api/act` | `{index}` lub `{prompt}` |
| `POST /api/agent/run` | Pętla agenta |

Zobacz też [control-layer.md](control-layer.md) — port **8219** to osobne REST DSL (`rest2imgl`), nie mylić z web UI na 8008.
