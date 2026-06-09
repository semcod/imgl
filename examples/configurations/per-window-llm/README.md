# Konfiguracja: LLM per okno (wycinek)

Vision LLM dostaje **tylko wycięty region** — najlepsza jakość na złożonych zrzutach.

## Problem bez per-window

```bash
imgl interact screen.png --llm   # na całym ekranie
```

Katalog może zawierać jednocześnie: `Projects` (GitHub), `Terminal` (IDE), `allama` (repo), `Python 3.13` (status bar).

## Rozwiązanie

```bash
# 1. Zobacz regiony
imgl windows screen.png --export-crops --annotate

# 2. LLM na jednym regionie
imgl interact screen.png --llm --window region-top --annotate --open
```

## Jak to działa (technicznie)

1. `window_scope.discover_windows()` → `region-top`, `region-bottom`
2. `crop_window_image()` — wycinek PNG regionu
3. `_call_vision_llm(crop_bbox=window.bbox)` — LLM widzi tylko crop
4. `_llm_json_to_options(origin_x, origin_y)` — współrzędne na pełnym zrzucie
5. `_snap_options_to_scene(window_id=...)` — dopasowanie do OCR w regionie

## Interaktywny wybór

```bash
imgl interact screen.png --llm
# → lista okien
# → wpisz 1 (region-top) lub 2 (region-bottom)
```

## Mapa numerów per okno

```bash
imgl interact screen.png --llm --window region-top --annotate
# → screen.region-top.numbered.png
```

## Konfiguracja Python

```python
from imgl.catalog import build_interactive_catalog
from imgl.window_scope import apply_discovered_windows, get_discovered_window

scene = analyze("screen.png", lang="eng+pol")
scene = apply_discovered_windows(scene)
window = get_discovered_window(scene, "region-top")

catalog = build_interactive_catalog(
    scene,
    image_path="screen.png",
    use_llm=True,
    window_id=window.id,
    llm_model="openrouter/google/gemini-2.5-flash",
)
```

## Powiązane

- [docs/vql-export.md](../../../docs/vql-export.md)
- [workflows/window-picker](../../workflows/window-picker/README.md)
- [platforms/gnome-wayland](../../platforms/gnome-wayland/README.md)
