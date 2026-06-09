# Workflow: capture → analyze → akcja

Podstawowa ścieżka od zrzutu ekranu do konkretnej akcji myszy/klawiatury.

## Krok 1 — Zrzut

```bash
imgl capture --interactive -o screen.png
imgl diagnose screen.png
```

Oczekiwany wynik diagnose: `worth_analyzing: true`. Jeśli `false` — zrzut jest pusty/czarny.

## Krok 2 — Analiza

```bash
imgl analyze screen.png -o screen.imgl.json --lang eng+pol
imgl vql screen.png -o layout.vql.json
```

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
  "text": "Projects"
}
```

## Krok 4 — Interaktywny shell (zalecane)

```bash
imgl interact screen.png -o layout.vql.json
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
# lub sucho:
imgl find screen.png --text Follow --click   # tylko JSON, bez execute
```

## Python API

```python
from imgl import analyze, actions

scene = analyze("screen.png", lang="eng+pol")
ui = actions(scene)

click = ui.click("button", text="Projects")
type_action = ui.type_into("hello", label="Type to search")
```

## Powiązane

- [integrations/python-api](../../integrations/python-api/README.md)
- [configurations/execute-desktop](../../configurations/execute-desktop/README.md)
