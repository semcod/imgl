# Zastosowanie: GitHub w przeglądarce

Przykład sterowania profilem GitHub (`github.com/wronai`) na zrzucie `screen.png`.

## Kontekst

Na pionowym zrzucie GitHub jest w **`region-top`** (górna połowa ekranu).

```bash
imgl windows screen.png --export-crops
# → screen.region-top.png  (zakładki, README, Repositories)
```

## Szybki start

```bash
export OPENROUTER_API_KEY=sk-or-...   # lub .env
imgl interact screen.png --llm --window region-top --annotate --open
```

## Typowy katalog LLM (region-top)

| # | Element | Akcja |
|---|---------|-------|
| 1 | Overview | click |
| 2 | Repositories | click |
| 3 | Projects | click |
| 9 | Type to search | click (fokus) → potem type |
| 11 | Follow | click |

## Przykładowe komendy w shellu

```
1                      # Overview
kliknij Projects       # zakładka Projects
kliknij Repositories   # lista repozytoriów
wpisz imgl w Type to search
mapa                   # screen.region-top.numbered.png
```

## URI VQL

```
vql://window/imgl?image=...&file=layout.vql.json&action=click&text=Projects&window=region-top&lang=eng%2Bpol
```

Via uri2vql:

```bash
uri2vql query 'vql://window/imgl?image=/path/screen.png&file=layout.vql.json&action=click&text=Projects&lang=eng%2Bpol'
```

## find (bez LLM)

```bash
imgl find screen.png --text Projects --click
imgl find screen.png --text Follow --click
```

## Uwagi

- Etykiety OCR mogą różnić się od wizualnych (`ff Projects` vs `Projects`) — LLM i snap OCR to korygują
- Po kliknięciu zakładki UI się zmienia → **nowy capture**
- Przyciski w README (`img2nl`, `nlp2cmd`) to linki — LLM je wykrywa jako klikalne

## Skrypt demo

```bash
examples/scripts/demo-github.sh screen.png
```

## Powiązane

- [workflows/window-picker](../../workflows/window-picker/README.md)
- [configurations/per-window-llm](../../configurations/per-window-llm/README.md)
