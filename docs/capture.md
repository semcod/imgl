# Capture — zrzut ekranu

imgl domyślnie próbuje **vdisplay mirror** (bez dialogu GNOME). Na Wayland, gdy mirror/driver zawiedzie, może automatycznie przejść na **portal GNOME** (wybór regionu).

Po capture imgl zapisuje **provenance** obok PNG (`screen.capture.json`) — metadane używane później przy eksporcie VQL i guardzie DISPLAY. Szczegóły: [vql-export.md](vql-export.md).

## Instalacja

```bash
cd ~/github/semcod/imgl
make install-dev          # imgl[capture] + editable vdisplay z ~/github/wronai/vdisplay
# lub ręcznie:
pip install -e ".[capture]"   # mss + vdisplay[pillow]
imgl install vdisplay       # pip install -e ~/github/wronai/vdisplay[pillow]
```

Opcjonalnie (nie wymagane do podstawowego capture):

```bash
pip install -e ~/github/oqlos/vql    # vql backend (tylko gdy IMGL_CAPTURE_ALLOW_VQL=1)
```

## Komendy

| Komenda | Zachowanie |
|---------|------------|
| `make capture-interactive` | mirror → auto portal fallback (Wayland) → `screen.png` + `--verify` |
| `make capture-analyze` | jak wyżej + `--analyze` (VQL + `.capture.json`) |
| `imgl capture -o screen.png` | to samo bez make (portal fallback domyślnie na Wayland) |
| `imgl capture -o screen.png --verify --analyze` | capture + OCR/layout + `screen.vql.json` |
| `imgl capture --analyze --vql-out layout.vql.json` | własna ścieżka VQL |
| `imgl capture --portal -o screen.png` | wymusza portal GNOME (region picker) |
| `imgl capture --interactive -o screen.png` | alias `--portal` (deprecated, ostrzeżenie) |
| `imgl capture --smart -o screen.png` | pełna kolejka + invalidacja cache OCR/VQL |
| `imgl verify screen.png` | sprawdza czy plik się zmienił i nie jest pusty |

### Capture + VQL w jednym kroku

```bash
imgl capture -o screen.png --verify --analyze --lang eng+pol
```

Tworzy:

- `screen.png` — zrzut
- `screen.capture.json` — method, display, monitor (vdisplay)
- `screen.vql.json` — VQLProgram
- `screen.vql.imgl.json` — cache Scene (imgl)

Następnie automatyzacja LLM:

```bash
imgl interact screen.png --llm --execute
```

## Kolejność backendów

1. **vdisplay mirror** (`prefer_mirror=True`) — bez portalu, wymaga grupy `video` dla driver-level
2. **vdisplay + portal** w łańcuchu (gdy `IMGL_CAPTURE_VDISPLAY_PORTAL=1` lub portal fallback)
3. **gnome-shell** (D-Bus) / **grim** / **gnome-screenshot** / **scrot**
4. **vql** — tylko gdy `IMGL_CAPTURE_ALLOW_VQL=1`
5. **GNOME portal** — `--portal` lub auto fallback na Wayland

Implementacja: `imgl/capture.py` → `vdisplay.capture.host.capture_host_to_file`.

## Sidecar provenance

Każdy udany capture zapisuje `*.capture.json` (moduł `imgl/capture_provenance.py`):

| Pole | Przykład | Znaczenie |
|------|----------|-----------|
| `method` | `mirror`, `drm+crop`, `portal` | Backend capture |
| `display` | `:0` | DISPLAY użyty przy zrzucie |
| `monitor` | `1` | Indeks monitora |
| `source` / `monitor_name` | `DP-1` | Nazwa outputu |
| `region` | `{x,y,width,height}` | Crop monitora |

Przy `imgl analyze` provenance trafia do `Scene.metadata.capture` i do `layout.vql.json`.

## Zmienne środowiskowe

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `IMGL_CAPTURE_PORTAL_FALLBACK` | `1` na Wayland | Po nieudanym mirror → portal GNOME |
| `IMGL_CAPTURE_PREFER_MIRROR` | `1` | Priorytet vdisplay mirror przed portalem |
| `IMGL_CAPTURE_VDISPLAY_PORTAL` | jak portal fallback | vdisplay z portalem w łańcuchu |
| `IMGL_CAPTURE_ALLOW_VQL` | wyłączone | Włącza backend vql |
| `IMGL_CAPTURE_SOURCE` | — | Output vdisplay (np. `DP-1`) |
| `IMGL_CAPTURE_TARGET` | — | Target mirror vdisplay |
| `VDISPLAY_CAPTURE_ALLOW_PORTAL` | — | Przekazywane do vdisplay |
| `IMGL_STRICT_DISPLAY` | wyłączone | Przy execute: blokuj gdy DISPLAY ≠ capture display |

## Wayland — typowe problemy

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `Driver-level capture failed` | Brak grupy `video` | `sudo usermod -aG video $USER` + re-login |
| Czarny zrzut | framebuffer niedostępny | `imgl capture --portal` lub portal fallback |
| `grim` / `gnome-screenshot` failed | brak narzędzi / timeout / Mutter | portal lub włącz Screen Recording |
| `AccessDenied` / portal response=2 | brak Screen Recording dla aplikacji | Settings → Privacy → Screen Recording → Cursor/terminal |
| Dialog GNOME | portal fallback | normalne — wybierz region ekranu |
| vdisplay not installed | brak pakietu | `make install-dev` lub `imgl install vdisplay` |

## Weryfikacja zrzutu

```bash
imgl capture -o screen.png --verify
imgl diagnose screen.png
# oczekuj: worth_analyzing: true
```

Jeśli `diagnose` zwraca blank — nie analizuj. Zrób nowy capture.

Sprawdzenie provenance:

```bash
cat screen.capture.json
jq '.metadata.capture' screen.vql.json
```

## Powiązane

- [vql-export.md](vql-export.md) — format VQL, relations, window_os, execute guard
- [platforms/gnome-wayland](../examples/platforms/gnome-wayland/README.md)
- [workflows/capture-to-action](../examples/workflows/capture-to-action/README.md)
- [control-layer.md](control-layer.md) — `make execute-llm` wymaga wcześniejszego zrzutu
