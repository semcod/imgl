# Zastosowanie: dialogi i formularze

Małe okna dialogowe (Settings, Save/Cancel, pola Username/Password) — najlepszy przypadek dla imgl.

## Dlaczego formularze działają dobrze

- Mało elementów, czytelne etykiety
- Wyraźne przyciski i pola input
- Jeden region = cały dialog (bez window picker)

## Przykład testowy (wbudowany w testy)

Scena `win-settings` z testów:

```
[WINDOW]  Settings
[BUTTON]  Save
[INPUT]   Username  (wartość: tom)
```

## Analiza zrzutu dialogu

```bash
imgl capture --interactive -o dialog.png
imgl annotate dialog.png --open
imgl interact dialog.png
```

## Typowe komendy

```
kliknij Save
wpisz alice w Username
2                    # numer pola input
mapa
```

## Python

```python
from imgl import analyze, actions

scene = analyze("dialog.png", lang="eng+pol")
ui = actions(scene)

ui.click("button", text="Save")
ui.type_into("alice", label="Username")
```

## find CLI

```bash
imgl find dialog.png --text Save --click
imgl find dialog.png --label Username --type-into alice
```

## HTML export (selektory tekstowe)

```bash
imgl html dialog.png -o dialog.html --embed-image
```

W HTML elementy mają `data-text="Save"`, `data-type="button"` — przydatne do automatyzacji opartej na DOM-like selektorach.

## Wskazówki

- Dialog na jednolitym tle → detekcja okien zwykle zwraca 1 region
- Unikaj półprzezroczystych overlay — OCR gorszy
- Po `Save` dialog znika → nowy capture

## Powiązane

- [workflows/capture-to-action](../../workflows/capture-to-action/README.md)
- [configurations/ocr-filtered](../../configurations/ocr-filtered/README.md)
