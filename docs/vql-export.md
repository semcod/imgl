# VQL — eksport i integracja z vdisplay

imgl używa standardu **VQL** ([oqlos/vql](https://github.com/oqlos/vql)) jako formatu interoperacji. Model wewnętrzny to **`Scene`**; eksport to **`VQLProgram`-compatible JSON**.

## Role projektów

| Warstwa | Projekt | Co robi |
|---------|---------|---------|
| Capture | **vdisplay** | PNG z host / mirror / virtual display + metadane OS (okna WM) |
| Semantyka | **imgl** | OCR, detekcja UI, katalog interakcji, współrzędne |
| Eksport | **imgl** → VQL | `layout.vql.json` — warstwy, relations, provenance |
| Protokół | **vql** / **uri2vql** | `vql://window/imgl?action=…` — bus dla agentów |
| Automatyzacja | **imgl** + LLM | katalog → URI → `execute` (xdotool) |

vdisplay **nie generuje VQL** — dostarcza piksele i prawdę OS. VQL powstaje po `imgl analyze` lub `imgl capture --analyze`.

## Pliki obok zrzutu

Dla `screen.png`:

| Plik | Format | Zawartość |
|------|--------|-----------|
| `screen.png` | PNG | Zrzut ekranu |
| `screen.capture.json` | JSON | Provenance capture (method, display, monitor, region…) |
| `screen.captured_at` | tekst | Timestamp świeżości zrzutu |
| `screen.vql.json` | VQLProgram | Eksport do agentów / uri2vql |
| `screen.vql.imgl.json` | Scene (imgl) | Cache analizy (OCR, okna, elementy) |

Przy odświeżeniu PNG cache VQL (`.vql.json`, `.vql.imgl.json`) jest czyszczony (`clear_vql_cache`). Provenance `.capture.json` pozostaje przy PNG do czasu nowego capture.

## Provenance capture (`screen.capture.json`)

Po każdym udanym `imgl capture` zapisywany jest sidecar z metadanymi backendu (głównie vdisplay):

```json
{
  "path": "/home/user/screen.png",
  "method": "mirror",
  "display": ":0",
  "monitor": 1,
  "source": "DP-1",
  "monitor_name": "DP-1",
  "width": 2560,
  "height": 1600
}
```

Przy `analyze()` imgl dołącza to do `Scene.metadata.capture` i propaguje do `layout.vql.json` → `metadata.capture`.

Moduł: `imgl/capture_provenance.py`

## Enrichment vdisplay (okna OS)

Gdy vdisplay jest zainstalowany, `analyze()` koreluje okna WM z regionami vision (IoU ≥ 0.3):

- `Scene.metadata.window_os` — mapa `{vision_window_id → app_label, os_window_id, monitor_name, vision_iou}`
- w VQL obiekty warstwy `windows` dostają `metadata.app_label`, `metadata.os_window_id`

Diagnostyka ręczna: `imgl map --image screen.png` lub `imgl doctor --full`.

## Struktura VQLProgram (imgl export)

Warstwy:

| `layer.id` | Zawartość |
|------------|-----------|
| `screen_regions` | opcjonalnie, `--with-grid` (wymaga pakietu `vql`) |
| `windows` | regiony okien + metadane OS |
| `ui_elements` | przyciski, inputy, panele |
| `text_regions` | bbox OCR |

Relations: `scene.relations[]` z `kind: "contains"` (okno → element, hierarchia bbox).

Przykład metadata w eksporcie:

```json
{
  "source": "imgl",
  "capture": { "method": "mirror", "display": ":0" },
  "window_os": {
    "win-main": { "app_label": "Cursor", "window_id": "0xabc", "vision_iou": 0.85 }
  },
  "by_role": { "button": 3, "input": 1 }
}
```

## Komendy CLI

```bash
# Capture + analiza + VQL w jednym kroku
imgl capture -o screen.png --verify --analyze --lang eng+pol
# → screen.png, screen.vql.json, screen.vql.imgl.json, screen.capture.json

# Osobno
imgl capture -o screen.png --verify
imgl vql screen.png -o layout.vql.json

# Eksport z siatką kolorów (vql package)
imgl vql screen.png -o layout.vql.json --with-grid
```

Python:

```python
from imgl import analyze, scene_to_vql, write_vql_program

scene = analyze("screen.png", lang="eng+pol")
program = scene_to_vql(scene)
write_vql_program(scene, "layout.vql.json")
```

## Guard DISPLAY przy execute

Akcje z `interact` / `resolve_imgl_uri` zawierają `image_path`. Przed kliknięciem `execute_action` porównuje `DISPLAY` z `screen.capture.json`:

| Zachowanie | Ustawienie |
|------------|------------|
| Ostrzeżenie w message | domyślnie |
| Blokada wykonania | `IMGL_STRICT_DISPLAY=1` |

Typowy przypadek: zrzut z `:99` (Xvfb), execute na `:0` — współrzędne się nie zgadzają.

## Integracja uri2vql

```bash
uri2vql adopt-imgl --image screen.png --out layout.vql.json --lang eng+pol
uri2vql query 'vql://window/imgl?image=screen.png&file=layout.vql.json&action=click&text=Save'
```

Szczegóły: [examples/integrations/uri2vql](../examples/integrations/uri2vql/README.md)

## Przepływ LLM (pełny)

```
vdisplay.capture_host_to_file → screen.png + .capture.json
         ↓
imgl.analyze → Scene (+ window_os) → layout.vql.json
         ↓
build_interactive_catalog (--llm) → numerowane akcje
         ↓
prompt_to_imgl_uri / agent → vql://window/imgl?click…
         ↓
resolve_imgl_uri → {x, y, image_path} → execute (xdotool)
```

Pętla agenta: **nowy capture po każdej akcji** — [workflows/multi-step-agent](../examples/workflows/multi-step-agent/README.md).

## Walidacja (oqlos/vql)

Po zapisie `write_vql_program` opcjonalnie waliduje program przez `VQLProgram.validate()` oraz `validate_program_metadata()` (gdy pakiet `vql` zainstalowany):

Schema metadanych imgl: `oqlos/vql` → `src/vql/schema/program_metadata_imgl.json` (`capture`, `window_os`).

```bash
pip install -e ~/github/oqlos/vql
imgl vql screen.png -o layout.vql.json   # ostrzeżenia na stderr przy błędach
IMGL_VALIDATE_VQL=0 imgl vql screen.png  # wyłączenie walidacji
```

## Powiązane

- [capture.md](capture.md) — backendy zrzutu, Wayland
- [architecture.md](architecture.md) — podział odpowiedzialności
- [control-layer.md](control-layer.md) — DSL `CAPTURE` / `ANALYZE` / `EXECUTE`
