# X11 (Linux)

Na sesji X11 capture i automatyzacja są prostsze niż na Wayland.

## Zalety X11 dla imgl

- `mss` zwykle działa bez portalu
- `xdotool` klika we współrzędne globalne ekranu
- Mniej problemów z skalowaniem DPI (przy jednym monitorze)

## Instalacja

```bash
pip install -e ".[capture,llm]"
sudo apt install tesseract-ocr tesseract-ocr-pol xdotool
```

## Capture

```bash
# mss / vdisplay — zwykle wystarczy
imgl capture -o screen.png --verify

# portal GNOME (gdy mirror nie działa)
imgl capture --portal -o screen.png
```

## Pełny workflow

```bash
imgl diagnose screen.png
imgl windows screen.png --export-crops
imgl interact screen.png --llm --window region-top
imgl interact screen.png --execute   # xdotool
```

## Side-by-side (dwa okna obok siebie)

Gdy masz dwa okna **obok siebie** (nie jeden pod drugim), `window_scope` wykrywa układ `side_by_side`:

```
region-left   — lewa aplikacja
region-right  — prawa aplikacja
```

Przykład: edytor po lewej, przeglądarka po prawej na jednym monitorze.

## DPI / wiele monitorów

Współrzędne w katalogu są w pikselach **zrzutu**. Przy mixed-DPI:

1. Rób capture i execute w tej samej sesji
2. Nie skaluj PNG przed analizą
3. Po zmianie rozdzielczości — nowy capture

## Powiązane

- [configurations/execute-desktop](../../configurations/execute-desktop/README.md)
- [workflows/capture-to-action](../../workflows/capture-to-action/README.md)
