# GNOME + Wayland (Linux)

Typowa konfiguracja na Ubuntu/Fedora z sesją Wayland. To środowisko, w którym powstaje większość zrzutów w repo (`screen.png`).

## Problemy specyficzne dla Wayland

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `Driver-level capture failed` | Brak grupy `video` | `sudo usermod -aG video $USER` + re-login |
| Czarny zrzut z `mss` | Brak dostępu do framebuffera | `imgl capture --portal` lub auto fallback |
| Dialog GNOME przy capture | Portal fallback po nieudanym mirror | Wybierz region — normalne zachowanie |
| `xdotool` nie klika we właściwe miejsce | Ograniczenia Wayland | X11 sesja, lub `ydotool` (uinput) |
| Logi Chrome przy `--open` | Przeglądarka otwiera PNG | Normalne — ignoruj Vulkan/GCM |
| Wysoki pionowy zrzut (2700×4800) | Scalenie monitorów / długi scroll | `window_scope` dzieli na `region-top` / `region-bottom` |

## Instalacja

```bash
make install-dev    # imgl[capture] + vdisplay z ~/github/wronai/vdisplay

sudo apt install tesseract-ocr tesseract-ocr-pol
sudo apt install xdotool             # opcjonalnie --execute
```

Driver-level mirror (bez portalu):

```bash
sudo usermod -aG video $USER
# wyloguj i zaloguj ponownie
```

## Capture

```bash
# Zalecane — mirror bez dialogu; na Wayland auto fallback do portalu GNOME
make capture-interactive
# lub:
imgl capture -o screen.png --verify

# Wymuszenie portalu (region picker)
imgl capture --portal -o screen.png

# Sprawdź czy zrzut ma treść (nie jest czarny)
imgl diagnose screen.png
# oczekuj: "worth_analyzing": true
```

Szczegóły backendów i zmiennych środowiskowych: [docs/capture.md](../../../docs/capture.md).

Jeśli `diagnose` zwraca blank — nie analizuj. Zrób nowy capture lub użyj `--allow-blank` tylko do testów.

## Analiza i okna

Na pionowym zrzucie (przeglądarka u góry, IDE na dole):

```bash
imgl windows screen.png --export-crops --annotate --open
```

Typowy wynik:

| Region | Zawartość |
|--------|-----------|
| `region-top` | GitHub / przeglądarka |
| `region-bottom` | IDE (Windsurf, VS Code, Cursor) |

## Interakcja z LLM per okno

```bash
# .env z OPENROUTER_API_KEY w katalogu projektu
imgl interact screen.png --llm --window region-top --annotate --open
```

W shellu:

```
2          # numer elementu z katalogu
kliknij Follow
wpisz test w Type to search
mapa
okna       # wróć do wyboru regionu
quit
```

## Wykonanie akcji (ostrożnie)

```bash
make install-control   # nlp2imgl / dsl2imgl
# Wymaga zgodności zrzutu z aktualnym pulpitem
make execute-llm PROMPT='wpisz test w Chat input'
# lub interaktywnie:
imgl interact screen.png --window region-top --execute
```

Po każdej akcji UI się zmienia — zrób nowy `capture` przed kolejnym krokiem.

## Zalecana konfiguracja

```python
from imgl import ImglConfig, analyze

scene = analyze("screen.png", config=ImglConfig(
    lang="eng+pol",
    max_dim=2560,          # szybszy OCR na 4K/8K
    use_img2vql=True,      # jeśli img2vql zainstalowany lokalnie
    catalog_filter=True,
))
```

## Powiązane przykłady

- [workflows/window-picker](../../workflows/window-picker/README.md)
- [configurations/per-window-llm](../../configurations/per-window-llm/README.md)
- [applications/github-browser](../../applications/github-browser/README.md)
