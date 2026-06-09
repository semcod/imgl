# imgl — przykłady

Katalog demonstruje **imgl** w różnych systemach, konfiguracjach i zastosowaniach:
od zrzutu ekranu (vdisplay) → semantyczny layout → VQL → katalog akcji → URI → NL → opcjonalnie klik na pulpicie.

Dokumentacja rdzeniowa: [docs/README.md](../docs/README.md) · [docs/vql-export.md](../docs/vql-export.md) · [docs/capture.md](../docs/capture.md)

## Wymagania wspólne

```bash
cd ~/github/semcod/imgl
python -m venv .venv && source .venv/bin/activate
pip install -e ".[llm,capture]"   # OCR + interakcja + capture + opcjonalny LLM

# Tesseract (OCR)
sudo apt install tesseract-ocr tesseract-ocr-pol   # Debian/Ubuntu
```

Capture z vdisplay (Wayland mirror, bez dialogu GNOME):

```bash
make install-dev    # imgl[capture] + editable vdisplay
# lub: imgl install vdisplay
```

Opcjonalnie (integracje lokalne, nie na PyPI):

```bash
pip install -e ~/github/wronai/vdisplay[pillow]
pip install -e ~/github/oqlos/vql/packages/uri2vql
pip install -e ~/github/oqlos/vql
pip install -e ~/github/oqlos/vql/packages/img2vql
pip install -e ~/github/wronai/img2nl[analyze]
```

## Mapa przykładów

| Katalog | Co pokazuje |
|---------|-------------|
| [platforms/gnome-wayland](platforms/gnome-wayland/README.md) | GNOME + Wayland, vdisplay mirror + portal fallback |
| [platforms/x11](platforms/x11/README.md) | X11, `xdotool`, szybszy capture |
| [platforms/macos](platforms/macos/README.md) | macOS, Tesseract, ograniczenia automatyzacji |
| [workflows/capture-to-action](workflows/capture-to-action/README.md) | Pełna ścieżka: capture → VQL → klik |
| [workflows/window-picker](workflows/window-picker/README.md) | Wybór regionu okna, wycinki PNG |
| [workflows/multi-step-agent](workflows/multi-step-agent/README.md) | Pętla agenta: capture → act → capture |
| [workflows/web-ui](workflows/web-ui/README.md) | Web UI na :8008 — manual + autonomiczny agent |
| [applications/github-browser](applications/github-browser/README.md) | Sterowanie GitHub w przeglądarce |
| [applications/ide-editor](applications/ide-editor/README.md) | IDE (Windsurf/VS Code) — terminal, pliki |
| [applications/dialog-form](applications/dialog-form/README.md) | Formularze, pola input, Save/Cancel |
| [configurations/ocr-filtered](configurations/ocr-filtered/README.md) | Domyślny filtr szumu OCR |
| [configurations/llm-vision](configurations/llm-vision/README.md) | Katalog z vision LLM (OpenRouter) |
| [configurations/per-window-llm](configurations/per-window-llm/README.md) | LLM tylko na wycinku wybranego okna |
| [configurations/execute-desktop](configurations/execute-desktop/README.md) | `--execute`, xdotool, guard DISPLAY |
| [integrations/uri2vql](integrations/uri2vql/README.md) | `vql://window/imgl` przez uri2vql |
| [integrations/nlp2uri](integrations/nlp2uri/README.md) | NL → URI → akcja |
| [integrations/python-api](integrations/python-api/README.md) | API Python: analyze, VQL, actions, catalog |
| [scripts](scripts/README.md) | Gotowe skrypty demonstracyjne |

## Szybki start (30 sekund)

```bash
# 1. Zrzut + analiza + VQL (jeden krok)
make install-dev
make capture-analyze
# lub: imgl capture -o screen.png --verify --analyze --lang eng+pol

# 2. Wykryte okna + wycinki
imgl windows screen.png --export-crops --annotate

# 3. Interakcja z LLM na regionie GitHub
export OPENROUTER_API_KEY=sk-or-...   # lub .env w katalogu imgl
imgl interact screen.png --llm --window region-top --execute
```

## Architektura

```
vdisplay.capture_host_to_file
         │
         ▼
screen.png + screen.capture.json   (provenance: method, display, monitor)
         │
         ▼
imgl analyze / load_or_analyze     (+ window_os z vdisplay, gdy dostępny)
         │
         ├─► screen.vql.json        (VQLProgram: warstwy, relations, metadata)
         ├─► screen.vql.imgl.json   (cache Scene — szybsze list/click)
         └─► Scene: windows, elements, ocr_boxes
                 │
                 ├─► window_scope.discover_windows()  → region-top, region-bottom, …
                 ├─► build_interactive_catalog()      → numerowana lista akcji
                 │       └─► refine_catalog_with_llm() (opcjonalnie, per-window crop)
                 ├─► nlp2uri / numer / URI            → vql://window/imgl?action=click
                 └─► execute_action()                 → xdotool (+ guard DISPLAY)
```

## Pliki wyjściowe

Dla `screen.png`:

| Plik | Opis |
|------|------|
| `screen.capture.json` | Provenance capture (vdisplay method, DISPLAY, monitor) |
| `screen.captured_at` | Timestamp świeżości zrzutu |
| `screen.vql.json` | VQLProgram (`metadata.capture`, `window_os`, `scene.relations`) |
| `screen.vql.imgl.json` | Cache Scene (OCR) — przy `vql_file=screen.vql.json` |
| `screen.numbered.png` | Mapa numerów katalogu na całym zrzucie |
| `screen.region-top.png` | Wycinek regionu `region-top` |
| `screen.region-top.numbered.png` | Podgląd regionu z numerem |

Przy własnym `-o layout.vql.json` cache to `layout.vql.imgl.json`.

## Skrypty

```bash
examples/scripts/demo-windows.sh screen.png
examples/scripts/demo-github.sh screen.png
examples/scripts/demo-nlp2uri.py screen.png
examples/scripts/demo-agent-loop.sh
```

## Zobacz też

- [README.md](../README.md) — instalacja i API
- [docs/vql-export.md](../docs/vql-export.md) — format VQL, provenance, execute guard
- [docs/architecture.md](../docs/architecture.md) — podział imgl / vdisplay / vql
- [CHANGELOG.md](../CHANGELOG.md) — historia zmian
