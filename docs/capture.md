# Capture — zrzut ekranu

imgl domyślnie próbuje **vdisplay mirror** (bez dialogu GNOME). Na Wayland, gdy mirror/driver zawiedzie, może automatycznie przejść na **portal GNOME** (wybór regionu).

## Instalacja

```bash
cd ~/github/semcod/imgl
make install-dev          # imgl[capture] + editable vdisplay z ~/github/wronai/vdisplay
# lub ręcznie:
pip install -e ".[capture]"   # mss + vdisplay[pillow]
```

Opcjonalnie (nie wymagane do podstawowego capture):

```bash
pip install -e ~/github/oqlos/vql    # vql backend (tylko gdy IMGL_CAPTURE_ALLOW_VQL=1)
```

## Komendy

| Komenda | Zachowanie |
|---------|------------|
| `make capture-interactive` | mirror → auto portal fallback (Wayland) → `screen.png` + `--verify` |
| `imgl capture -o screen.png` | to samo bez make (portal fallback domyślnie na Wayland) |
| `imgl capture --portal -o screen.png` | wymusza portal GNOME (region picker) |
| `imgl capture --interactive -o screen.png` | alias `--portal` (deprecated, ostrzeżenie) |
| `imgl capture --smart -o screen.png` | `make capture` — pełna kolejka backendów |
| `imgl verify screen.png` | sprawdza czy plik się zmienił i nie jest pusty |

## Kolejność backendów

1. **vdisplay mirror** (`prefer_mirror=True`) — bez portalu, wymaga grupy `video` dla driver-level
2. **vdisplay + portal** w łańcuchu (gdy `IMGL_CAPTURE_VDISPLAY_PORTAL=1` lub portal fallback)
3. **gnome-shell** (D-Bus) / **grim** / **gnome-screenshot** / **scrot**
4. **vql** — tylko gdy `IMGL_CAPTURE_ALLOW_VQL=1`
5. **GNOME portal** — `--portal` lub auto fallback na Wayland

## Zmienne środowiskowe

| Zmienna | Domyślnie | Opis |
|---------|-----------|------|
| `IMGL_CAPTURE_PORTAL_FALLBACK` | `1` na Wayland | Po nieudanym mirror → portal GNOME |
| `IMGL_CAPTURE_PREFER_MIRROR` | `1` | Priorytet vdisplay mirror przed portalem |
| `IMGL_CAPTURE_VDISPLAY_PORTAL` | jak portal fallback | vdisplay z portalem w łańcuchu |
| `IMGL_CAPTURE_ALLOW_VQL` | wyłączone | Włącza backend vql |
| `VDISPLAY_CAPTURE_ALLOW_PORTAL` | — | Przekazywane do vdisplay |

## Wayland — typowe problemy

| Objaw | Przyczyna | Rozwiązanie |
|-------|-----------|-------------|
| `Driver-level capture failed` | Brak grupy `video` | `sudo usermod -aG video $USER` + re-login |
| Czarny zrzut | framebuffer niedostępny | `imgl capture --portal` lub portal fallback |
| `grim` / `gnome-screenshot` failed | brak narzędzi / timeout / Mutter | portal lub włącz Screen Recording |
| `AccessDenied` / portal response=2 | brak Screen Recording dla aplikacji | Settings → Privacy → Screen Recording → Cursor/terminal |
| Dialog GNOME | portal fallback | normalne — wybierz region ekranu |

## Weryfikacja zrzutu

```bash
imgl capture -o screen.png --verify
imgl diagnose screen.png
# oczekuj: worth_analyzing: true
```

Jeśli `diagnose` zwraca blank — nie analizuj. Zrób nowy capture.

## Powiązane

- [platforms/gnome-wayland](../examples/platforms/gnome-wayland/README.md)
- [workflows/capture-to-action](../examples/workflows/capture-to-action/README.md)
- [control-layer.md](control-layer.md) — `make execute-llm` wymaga wcześniejszego zrzutu
