# Konfiguracja: OCR + filtr szumu (domyślna)

Domyślny tryb bez LLM — szybki, offline, oparty na Tesseract + heurystykach.

## Włączenie

```bash
imgl interact screen.png              # filtr ON (domyślnie)
imgl interact screen.png --no-filter  # wszystkie detekcje OCR
```

## Co robi filtr (`catalog_filter.py`)

- Zachowuje wpisy `window`
- Usuwa szum: pojedyncze znaki, fragmenty kodu, duplikaty
- Limit `max_items=40` (konfigurowalne w `ImglConfig.catalog_max_items`)

## Kiedy używać

| Sytuacja | Flaga |
|----------|-------|
| Szybki podgląd, mały dialog | domyślnie (filtr ON) |
| Debug OCR, pełna lista | `--no-filter` |
| Duży ekran IDE | `--window region-bottom` + filtr |
| Czysty UI (GitHub) | `--llm` zamiast samego filtra |

## Python

```python
from imgl import ImglConfig, analyze
from imgl.catalog import build_interactive_catalog

scene = analyze("screen.png", config=ImglConfig(
    lang="eng+pol",
    catalog_filter=True,
    catalog_max_items=40,
))

catalog = build_interactive_catalog(
    scene,
    image_path="screen.png",
    filter_noise=True,
    use_llm=False,
)
```

## Porównanie na screen.png (cały ekran)

| Tryb | ~liczba pozycji |
|------|-----------------|
| `--no-filter` | 45+ |
| filtr (domyślny) | ~24 |
| `--llm --window region-top` | ~15–20 (sensowne) |

## Powiązane

- [configurations/llm-vision](../llm-vision/README.md)
- [workflows/window-picker](../../workflows/window-picker/README.md)
