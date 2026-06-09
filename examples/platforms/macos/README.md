# macOS

imgl działa na macOS (OCR, analiza, eksport, interaktywny shell). Automatyzacja pulpitu jest ograniczona.

## Co działa

| Funkcja | macOS |
|---------|-------|
| `imgl analyze` / `html` / `svg` / `vql` | tak |
| `imgl interact` / `annotate` / `windows` | tak |
| `imgl capture` (mss) | tak (uprawnienia Screen Recording) |
| `--llm` (OpenRouter) | tak |
| `--execute` (xdotool) | nie — brak xdotool; użyj osobnego bridge |

## Instalacja

```bash
brew install tesseract tesseract-lang
pip install -e ".[capture,llm]"
```

Uprawnienia: **System Settings → Privacy → Screen Recording** dla terminala/IDE.

## Capture

```bash
imgl capture -o screen.png
imgl capture -o screen.png --verify --analyze   # + VQL (bez vdisplay na macOS)
imgl diagnose screen.png
```

## Analiza i katalog

```bash
imgl windows screen.png --export-crops --annotate
imgl interact screen.png --llm --window region-top
```

Mapa numerów otworzy się w Podglądzie (`open`):

```bash
imgl annotate screen.png --open
```

## Automatyzacja na macOS

`imgl execute` szuka `xdotool` / `ydotool` — na macOS użyj:

1. **Dry-run** — `imgl interact` bez `--execute`, kopiuj współrzędne
2. **Własny bridge** — np. AppleScript, `cliclick`, Hammerspoon
3. **Agent zewnętrzny** — koru / Cursor wykonuje akcje po URI

Przykład odczytu akcji bez wykonania:

```bash
imgl find screen.png --text Save --click
# {"action": "click", "x": 310, "y": 206, ...}
```

## Powiązane

- [docs/vql-export.md](../../../docs/vql-export.md)
- [integrations/python-api](../../integrations/python-api/README.md)
- [workflows/multi-step-agent](../../workflows/multi-step-agent/README.md)
