# Architektura — kto za co odpowiada

## Projekty

| Projekt | Rola | NL → klik na zrzucie? |
|---------|------|------------------------|
| **imgl** | Zrzut → Scene → katalog → VQL → współrzędne → execute | **TAK (rdzeń)** |
| **vdisplay** | Capture PNG z host/mirror/virtual display; lista okien OS (WM) | NIE (transport) |
| **vql** | `VQLProgram` schema, opcjonalny portal capture, bus `vql://window/*` | NIE (infrastruktura) |
| **nlp2uri** (semcod) | NL → `app://`, `file://`, `desktop-*://` | Częściowo (delegacja do imgl) |
| **img2nl** | Opis sceny, blank check | NIE |

## Warstwa kontroli imgl (`packages/`)

Wszystkie adaptery delegują do **`dsl2imgl.dispatch()`** — jeden bus, wiele wejść:

```
nlp2imgl / uri2imgl / cli2imgl / mcp2imgl / rest2imgl
                    ↓
               dsl2imgl.dispatch()
                    ↓
         imgl/capture, pipeline, nlp2uri, execute
```

**Web UI** (`imgl serve :8008`) omija DSL — bezpośrednio używa `imgl/web/session.py`.

## Przepływ capture → VQL → LLM → execute

```
┌─────────────┐     screen.png + .capture.json
│  vdisplay   │ ──────────────────────────────►
└─────────────┘
       │
       ▼
┌─────────────┐     Scene (.vql.imgl.json)
│ imgl.analyze│ ──► layout.vql.json (VQLProgram)
│ + provenance│     metadata.capture, window_os, relations
└─────────────┘
       │
       ▼
┌─────────────┐     vql://window/imgl?action=click&text=…
│ katalog LLM │ ──► {x, y, image_path}
│ interact    │
└─────────────┘
       │
       ▼
┌─────────────┐     xdotool (DISPLAY guard)
│   execute   │
└─────────────┘
```

### Kroki `kliknij Projects`

1. `imgl capture --analyze` (vdisplay mirror) → `screen.png` + `.capture.json` + `.vql.json`
2. `build_interactive_catalog` (+ opcjonalnie vision LLM) → numerowane akcje
3. `imgl/nlp2uri.py` → `vql://window/imgl?action=click&text=Projects`
4. `imgl/interact.resolve_imgl_uri` → `{action, x, y, image_path}`
5. `imgl/execute.py` → xdotool (ostrzeżenie lub blokada przy mismatch DISPLAY)

Skrócony one-liner po capture:

```bash
imgl capture -o screen.png --verify --analyze
imgl interact screen.png --llm --execute
```

## Formaty danych

| Artefakt | Moduł | Konsument |
|----------|-------|-----------|
| `*.capture.json` | `capture_provenance` | VQL metadata, execute guard |
| Scene (`.vql.imgl.json`) | `types`, `pipeline` | katalog, cache OCR |
| VQLProgram (`.vql.json`) | `export/vql_adapter` | uri2vql, agenci zewnętrzni |
| URI `vql://window/imgl` | `uri`, `interact` | nlp2uri, dsl2imgl, REST |

Szczegóły VQL: [vql-export.md](vql-export.md).

## Zasada podziału

- **Piksele z ekranu** → **vdisplay** (imgl wywołuje jako pierwszy backend capture)
- **Semantyka UI** (OCR, bbox, katalog) → **imgl**
- **Eksport standardowy** → **VQL** (przez `scene_to_vql`)
- **Protokół URI / bus** → **vql** / **uri2vql**
- **NL ogólny desktop** (otwórz app, plik) → **nlp2uri**
- **Opis obrazu / blank** → **img2nl**

vdisplay **nie** opisuje zawartości zrzutu — to robi imgl. Korelacja okien OS ↔ vision (`vdisplay_bridge`) wzbogaca metadane VQL, nie zastępuje analizy.

## Integracja z Koru

Koru (`semcod/koru`) używa imgl jako transport wizyjny:

- `koru/integrations/imgl_client.py` — adapter do `nlp2imgl` / `rest2imgl`
- Fallback w `koru auto` gdy plugin koruide padnie (`KORU_IMGL_FALLBACK=1`)
- MCP `koru_desktop_uri_handle` z `transport=imgl`
- Verby `UI_*` w `dsl2coru`

Szczegóły: [koru/docs/imgl-integration.md](https://github.com/semcod/koru/blob/main/docs/imgl-integration.md)
