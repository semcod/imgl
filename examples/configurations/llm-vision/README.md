# Konfiguracja: vision LLM (OpenRouter)

Katalog elementów budowany przez model wizyjny zamiast samego OCR.

## Instalacja

```bash
pip install -e ".[llm]"
```

## Klucz API

```bash
# opcja A — export
export OPENROUTER_API_KEY=sk-or-v1-...

# opcja B — plik .env w katalogu imgl
echo 'OPENROUTER_API_KEY=sk-or-v1-...' >> .env
```

## Uruchomienie

```bash
imgl interact screen.png --llm
```

Komunikat sukcesu:

```
Katalog: vision LLM (openrouter/google/gemini-2.5-flash, okno=region-top, 19 elementów)
```

Fallback (brak klucza / litellm):

```
UWAGA: LLM niedostępny (...)
Katalog: fallback heurystyczny (filtrowany OCR)
```

## Model

Domyślny: `openrouter/google/gemini-2.5-flash`

Zmiana:

```bash
export IMGL_VISION_MODEL=openrouter/google/gemini-2.5-flash
```

lub w Python:

```python
ImglConfig(llm_vision_model="openrouter/google/gemini-2.5-flash", use_llm_catalog=True)
```

## Co daje LLM

| Zaleta | Opis |
|--------|------|
| Semantyka | `Projects` zamiast `ff Projects` |
| Mniej szumu | pomija linie kodu, plain text |
| Nowe elementy | `Teams`, `Insights` — niewidoczne w OCR |
| Snap do OCR | współrzędne z refined bbox po dopasowaniu |

## Ograniczenia

- Wymaga sieci i klucza API
- Koszt per screenshot
- Kolejność elementów może się zmieniać → preferuj **numery** lub **unikalne etykiety**
- Bez `--window` na wieloaplikacyjnym zrzucie — mieszanie regionów

## Zalecany wzorzec

```bash
imgl interact screen.png --llm --window region-top
```

## Powiązane

- [docs/vql-export.md](../../../docs/vql-export.md)
- [configurations/per-window-llm](../per-window-llm/README.md)
- [applications/github-browser](../../applications/github-browser/README.md)
