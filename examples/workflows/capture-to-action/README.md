# Workflow: capture → analyze → akcja

Podstawowa ścieżka od zrzutu ekranu do konkretnej akcji myszy/klawiatury.

## Krok 1 — Zrzut (+ opcjonalnie VQL)

```bash
# Zalecane: capture + analiza + VQL w jednym kroku
imgl capture -o screen.png --verify --analyze --lang eng+pol

# Lub osobno:
make capture-interactive   # imgl capture -o screen.png --verify
make capture-analyze       # + VQL + .capture.json
imgl diagnose screen.png
```

Po `--analyze` powstają:

| Plik | Opis |
|------|------|
| `screen.png` | Zrzut (vdisplay mirror / portal) |
| `screen.capture.json` | Provenance: method, display, monitor |
| `screen.vql.json` | VQLProgram (warstwy UI, relations, metadata) |
| `screen.vql.imgl.json` | Cache Scene (OCR) |

Oczekiwany wynik diagnose: `worth_analyzing: true`. Jeśli `false` — zrzut jest pusty/czarny.

Szczegóły formatów: [docs/vql-export.md](../../docs/vql-export.md).

## Krok 2 — Analiza (gdy bez `--analyze`)

```bash
imgl analyze screen.png -o screen.imgl.json --lang eng+pol
imgl vql screen.png -o layout.vql.json
```

`analyze()` automatycznie dołącza provenance z `.capture.json` i koreluje okna OS (vdisplay), gdy pakiet jest dostępny.

## Krok 3 — Znajdź element

```bash
# Lista wszystkich akcji
imgl find screen.png --list

# Klik w przycisk po tekście
imgl find screen.png --type button --text Save --click

# Wpisz w pole
imgl find screen.png --label Username --type-into alice
```

Wyjście JSON:

```json
{
  "action": "click",
  "x": 624,
  "y": 273,
  "element_id": "window_0-button-20",
  "element_type": "button",
  "text": "Projects",
  "image_path": "/path/to/screen.png"
}
```

Pole `image_path` umożliwia guard DISPLAY przy execute (porównanie z `screen.capture.json`).

## Krok 4 — Interaktywny shell (zalecane)

```bash
imgl interact screen.png --llm -o layout.vql.json
```

W shellu:

| Wejście | Efekt |
|---------|-------|
| `3` | wybierz element nr 3 z katalogu |
| `kliknij Save` | dopasowanie NL → URI → click |
| `wpisz hello w search` | type do pola input |
| `mapa` | PNG z numerami |
| `quit` | koniec |

## Krok 5 — Wykonanie (Linux)

```bash
imgl interact screen.png --execute
# DISPLAY mismatch → ostrzeżenie; blokada: IMGL_STRICT_DISPLAY=1
# lub sucho:
imgl find screen.png --text Follow --click   # tylko JSON, bez execute
```

## Python API

```python
from imgl import analyze, actions, scene_to_vql, write_vql_program

scene = analyze("screen.png", lang="eng+pol")
write_vql_program(scene, "layout.vql.json")

ui = actions(scene)
click = ui.click("button", text="Projects")
type_action = ui.type_into("hello", label="Type to search")
```

## Powiązane

- [docs/capture.md](../../docs/capture.md)
- [docs/vql-export.md](../../docs/vql-export.md)
- [integrations/python-api](../../integrations/python-api/README.md)
- [configurations/execute-desktop](../../configurations/execute-desktop/README.md)
