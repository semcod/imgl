# imgl — przykłady

Katalog demonstruje **imgl** w różnych systemach, konfiguracjach i zastosowaniach:
od zrzutu ekranu → semantyczny layout → katalog akcji → URI VQL → NL (`nlp2uri`) → opcjonalnie klik na pulpicie.

## Wymagania wspólne

```bash
cd ~/github/semcod/imgl
python -m venv .venv && source .venv/bin/activate
pip install -e ".[llm]"    # OCR + interakcja + opcjonalny LLM

# Tesseract (OCR)
sudo apt install tesseract-ocr tesseract-ocr-pol   # Debian/Ubuntu
```

Opcjonalnie (integracje lokalne, nie na PyPI):

```bash
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
| [workflows/capture-to-action](workflows/capture-to-action/README.md) | Pełna ścieżka: capture → analyze → klik |
| [workflows/window-picker](workflows/window-picker/README.md) | Wybór regionu okna, wycinki PNG |
| [workflows/multi-step-agent](workflows/multi-step-agent/README.md) | Pętla agenta: capture → act → capture |
| [workflows/web-ui](workflows/web-ui/README.md) | Web UI na :8008 — manual + autonomiczny agent |
| [applications/github-browser](applications/github-browser/README.md) | Sterowanie GitHub w przeglądarce |
| [applications/ide-editor](applications/ide-editor/README.md) | IDE (Windsurf/VS Code) — terminal, pliki |
| [applications/dialog-form](applications/dialog-form/README.md) | Formularze, pola input, Save/Cancel |
| [configurations/ocr-filtered](configurations/ocr-filtered/README.md) | Domyślny filtr szumu OCR |
| [configurations/llm-vision](configurations/llm-vision/README.md) | Katalog z vision LLM (OpenRouter) |
| [configurations/per-window-llm](configurations/per-window-llm/README.md) | LLM tylko na wycinku wybranego okna |
| [configurations/execute-desktop](configurations/execute-desktop/README.md) | `--execute`, xdotool/ydotool |
| [integrations/uri2vql](integrations/uri2vql/README.md) | `vql://window/imgl` przez uri2vql |
| [integrations/nlp2uri](integrations/nlp2uri/README.md) | NL → URI → akcja |
| [integrations/python-api](integrations/python-api/README.md) | API Python: analyze, actions, catalog |
| [scripts](scripts/) | Gotowe skrypty demonstracyjne |

## Szybki start (30 sekund)

```bash
# 1. Zrzut (lub użyj istniejącego screen.png)
make install-dev
make capture-interactive   # mirror → portal fallback na Wayland

# 2. Wykryte okna + wycinki
imgl windows screen.png --export-crops --annotate

# 3. Interakcja z LLM na regionie GitHub
export OPENROUTER_API_KEY=sk-or-...   # lub .env w katalogu imgl
imgl interact screen.png --llm --window region-top
```

## Architektura

```
zrzut PNG
   │
   ▼
imgl analyze / load_or_analyze
   │
   ├─► layout.vql.json      (program VQL)
   ├─► layout.imgl.json     (cache sceny)
   └─► Scene: windows, elements, ocr_boxes
           │
           ├─► window_scope.discover_windows()  → region-top, region-bottom, …
           │
           ├─► build_interactive_catalog()      → numerowana lista akcji
           │       └─► refine_catalog_with_llm() (opcjonalnie, per-window crop)
           │
           ├─► nlp2uri / numer / URI            → vql://window/imgl?action=click
           │
           └─► execute_action()                 → xdotool / ydotool (Linux)
```

## Pliki wyjściowe

| Plik | Opis |
|------|------|
| `layout.vql.json` | Program VQL (warstwy windows, ui_elements, text_regions) |
| `layout.imgl.json` | Cache sceny (szybsze `list`/`click` bez ponownego OCR) |
| `screen.numbered.png` | Mapa numerów katalogu na całym zrzucie |
| `screen.region-top.png` | Wycinek regionu `region-top` |
| `screen.region-top.numbered.png` | Podgląd regionu z numerem |

## Skrypty

```bash
examples/scripts/demo-windows.sh screen.png
examples/scripts/demo-github.sh screen.png
examples/scripts/demo-nlp2uri.py screen.png
examples/scripts/demo-agent-loop.sh
```

## Zobacz też

- [README.md](../README.md) — instalacja i API
- [CHANGELOG.md](../CHANGELOG.md) — historia zmian
