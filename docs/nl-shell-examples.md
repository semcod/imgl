# NL ze shell — wpisz w chat i wyślij

Scenariusz: Cursor/IDE, panel AI na dole, pole **Chat input** / „Add a follow-up”.

## 1. Przygotowanie

```bash
cd ~/github/semcod/imgl
make install-dev
make install-control

# zrzut (vdisplay mirror; portal fallback na Wayland)
make capture-interactive

# sprawdź regiony
imgl windows screen.png
# region-bottom = IDE, region-top = przeglądarka
```

## 2. Wpisz prompt do pola chat (NL)

### Interaktywnie (imgl)

```bash
imgl interact screen.png --llm --window region-bottom --execute
# w shellu:
wpisz opisz architekturę imgl w Chat input
```

### Jedna komenda (nlp2imgl)

```bash
nlp2imgl apply "wpisz opisz architekturę imgl w Chat input" \
  --image screen.png --window region-bottom
```

### DSL (dsl2imgl)

```bash
dsl2imgl exec 'TYPE "opisz architekturę imgl" IN "Chat input" IMAGE screen.png WINDOW region-bottom EXECUTE 1'
```

## 3. Wyślij — Ctrl+Enter lub Enter

### Ctrl+Enter (Cursor domyślnie)

```bash
nlp2imgl apply "naciśnij ctrl+enter" --execute
# lub
dsl2imgl exec 'KEY ctrl+Return EXECUTE 1'
# lub bezpośrednio
xdotool key ctrl+Return
```

### Sam Enter (gdy UI akceptuje Enter)

```bash
nlp2imgl apply "naciśnij enter" --execute
dsl2imgl exec 'KEY Return EXECUTE 1'
```

## 4. Pełna pętla (shell script)

```bash
#!/usr/bin/env bash
set -euo pipefail
IMAGE=screen.png
WINDOW=region-bottom
PROMPT="Wyjaśnij podział odpowiedzialności imgl vs vql"

imgl capture -o "$IMAGE" --verify

nlp2imgl apply "wpisz $PROMPT w Chat input" --image "$IMAGE" --window "$WINDOW"
sleep 0.3
nlp2imgl apply "naciśnij ctrl+enter" --execute

# odśwież zrzut po odpowiedzi
sleep 2
imgl capture -o "$IMAGE" --verify
```

## 5. REST (automatyzacja zewnętrzna)

```bash
rest2imgl serve --port 8219 &

curl -s -X POST http://127.0.0.1:8219/v1/nl \
  -H 'Content-Type: application/json' \
  -d "{\"prompt\":\"wpisz hello w Chat input\",\"image\":\"screen.png\",\"window\":\"$WINDOW\",\"execute\":true}"

curl -s -X POST http://127.0.0.1:8219/v1/nl \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"ctrl+enter","execute":true}'
```

## Uwagi

- Wymaga **xdotool** (Linux X11); na Wayland capture działa przez vdisplay mirror lub portal GNOME, klik może być ograniczony.
- Po każdej akcji zrób **nowy zrzut** — współrzędne ze starego PNG szybko się dezaktualizują.
- Jeśli brak **Chat input** w katalogu: użyj `--llm` lub `region-bottom`, szukaj pola **Chat input** / **Pole tekstowe**.
