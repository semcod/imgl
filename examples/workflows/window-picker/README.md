# Workflow: wybór okna / regionu

Gdy na zrzucie jest wiele aplikacji (np. przeglądarka + IDE), analizuj **jeden region naraz**.

## Dlaczego?

- OCR na całym 2700×4800 daje szum (setki fałszywych przycisków)
- LLM na całym ekranie miesza GitHub z terminalem
- Współrzędne i katalog są czytelniejsze per okno

## Wykrywanie regionów

```bash
imgl windows screen.png --export-crops --annotate
```

JSON na stdout:

```json
{
  "window_count": 2,
  "windows": [
    {"index": 1, "id": "region-top", "title": "…", "bbox": {"x": 0, "y": 0, "w": 2700, "h": 1850}},
    {"index": 2, "id": "region-bottom", "title": "…", "bbox": {"x": 0, "y": 2091, "w": 2700, "h": 2701}}
  ]
}
```

Pliki:

```
screen.region-top.png
screen.region-top.numbered.png
screen.region-bottom.png
screen.region-bottom.numbered.png
```

## Interaktywny wybór

```bash
imgl interact screen.png --llm
```

```
=== Wykryte okna (2) — wybierz region do analizy ===
  1. region-top     … GitHub
  2. region-bottom  … IDE

Co chcesz zrobić? 1
```

Komendy w fazie wyboru:

| Komenda | Efekt |
|---------|-------|
| `1` / `2` | wybierz region |
| `podglad` | wygeneruj wycinki PNG |
| `wszystkie` | katalog na całym ekranie (bez podziału) |
| `okna` | wróć do listy okien (w fazie akcji) |

## Bezpośredni wybór (bez promptu)

```bash
# GitHub (górny region)
imgl interact screen.png --llm --window region-top --annotate --open

# IDE (dolny region)
imgl interact screen.png --llm --window region-bottom
```

## Jak działa detekcja

Moduł `imgl/window_scope.py`:

1. **`stacked`** — okna jedno pod drugim (Twój `screen.png`) → podział poziomy
2. **`side_by_side`** — okna obok siebie → `region-left` / `region-right`
3. Gutter wybierany po **równowadze elementów** (nie po samym rozmiarze ciemnego pasa)

## LLM dostaje tylko wycinek

Przy `--window region-top` vision LLM widzi **tylko** `screen.region-top.png` (crop), a współrzędne są mapowane z powrotem na pełny zrzut.

## Powiązane

- [configurations/per-window-llm](../../configurations/per-window-llm/README.md)
- [applications/github-browser](../../applications/github-browser/README.md)
- [applications/ide-editor](../../applications/ide-editor/README.md)
