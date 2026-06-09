# Konfiguracja: wykonanie na pulpicie (`--execute`)

imgl może wykonać akcje `click` i `type` przez narzędzia Linux.

## Wymagania

```bash
sudo apt install xdotool    # X11 — zalecane
# lub
sudo apt install ydotool    # Wayland (uinput)
```

Sprawdź:

```bash
which xdotool ydotool
```

## Użycie

```bash
# Capture + VQL (zalecane przed execute)
imgl capture -o screen.png --verify --analyze

# Dry-run (domyślnie) — tylko JSON + komunikat
imgl interact screen.png --window region-top
# → Dry-run: click @ (624, 273)

# Wykonanie
imgl interact screen.png --window region-top --execute
# → Wykonano: click @ (624, 273) [xdotool]
```

## Guard DISPLAY

Przy execute imgl porównuje `$DISPLAY` z `screen.capture.json` (zapisanym przez vdisplay przy capture):

| Zachowanie | Ustawienie |
|------------|------------|
| Ostrzeżenie w message | domyślnie |
| Blokada wykonania | `IMGL_STRICT_DISPLAY=1` |

Typowy problem: zrzut z `:99` (Xvfb), klik na `:0` — współrzędne się nie zgadzają.

Payload akcji zawiera `image_path` (z `interact` / `resolve_imgl_uri`) — wymagane do guarda.

## Obsługiwane akcje

| action | execute |
|--------|---------|
| `click` | `mousemove` + `click 1` |
| `type` | `click` + `type --delay 12 -- TEXT` |

**Nieobsługiwane:** Tab, Enter, skróty klawiszowe, scroll, drag.

## Bezpieczeństwo

- Współrzędne muszą odpowiadać **aktualnemu** pulpitowi
- Zrzut sprzed 5 minut → klik w złe miejsce
- Zawsze: `capture --analyze` → `interact --execute` w jednej sesji

## Wayland vs X11

| Środowisko | Narzędzie |
|------------|-----------|
| X11 | `xdotool` — działa dobrze |
| Wayland | `xdotool` często zawodzi; spróbuj `ydotool` lub X11 session |

## find + ręczne wykonanie

```bash
imgl find screen.png --text Follow --click
# skopiuj x,y do własnego skryptu / xdotool mousemove ...
```

## Python

```python
from imgl.execute import execute_action

payload = {
    "action": "click",
    "x": 2261,
    "y": 523,
    "image_path": "/path/to/screen.png",
}
result = execute_action(payload, dry_run=False)
print(result.method, result.message)
```

## Powiązane

- [docs/vql-export.md](../../../docs/vql-export.md)
- [platforms/x11](../../platforms/x11/README.md)
- [workflows/multi-step-agent](../../workflows/multi-step-agent/README.md)
