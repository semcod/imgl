# Integracja: Python API

Pełny dostęp programistyczny do pipeline imgl.

## Analiza

```python
from imgl import analyze, ImglConfig, scene_to_json, actions

scene = analyze("screen.png", lang="eng+pol", config=ImglConfig(
    lang="eng+pol",
    max_dim=2560,
    use_img2vql=True,
    detect_inputs=True,
))

print(scene.width, scene.height)
print(len(scene.windows), "windows")

ui = actions(scene)
print(ui.click("button", text="Save"))
print(ui.type_into("alice", label="Username"))
```

## Katalog interaktywny

```python
from imgl.catalog import build_interactive_catalog, format_catalog_table
from imgl.window_scope import apply_discovered_windows, get_discovered_window

scene = apply_discovered_windows(scene)
window = get_discovered_window(scene, "region-top")

catalog = build_interactive_catalog(
    scene,
    image_path="screen.png",
    vql_file="layout.vql.json",
    lang="eng+pol",
    use_llm=True,
    window_id=window.id if window else None,
)

print(format_catalog_table(catalog))
```

## NL → URI → resolve

```python
from imgl.interact import InteractSession, resolve_imgl_uri
from imgl.nlp2uri import prompt_to_imgl_uri

session = InteractSession(
    image_path="screen.png",
    vql_file="layout.vql.json",
    lang="eng+pol",
    scene=scene,
    catalog=catalog,
    selected_window_id="region-top",
)

resolved = prompt_to_imgl_uri("kliknij Follow", image="screen.png", catalog=catalog)
result = resolve_imgl_uri(resolved.uri, session)
assert result["ok"]
print(result["x"], result["y"])
```

## Wykonanie

```python
from imgl.execute import execute_action

payload = {k: v for k, v in result.items() if k not in {"ok", "uri_action"}}
execute_action(payload, dry_run=True)   # test
# execute_action(payload, dry_run=False)  # xdotool
```

## Eksport

```python
from imgl import scene_to_html, scene_to_svg, write_vql_program

write_vql_program(scene, "layout.vql.json")
html = scene_to_html(scene, embed_image=True)
svg = scene_to_svg(scene, mode="overlay", background="screen.png")
```

## Mapa numerów

```python
from imgl.export import write_annotated_image
from imgl.window_scope import get_discovered_window

window = get_discovered_window(scene, "region-top")
write_annotated_image(
    scene, catalog, "screen.region-top.numbered.png",
    source_image="screen.png",
    window=window,
)
```

## Cache

```python
from imgl.scene_cache import load_or_analyze, save_scene_cache

scene = load_or_analyze("screen.png", vql_file="layout.vql.json", lang="eng+pol")
save_scene_cache(scene, "layout.vql.json")
```

## Powiązane

- [workflows/capture-to-action](../../workflows/capture-to-action/README.md)
- [configurations/per-window-llm](../../configurations/per-window-llm/README.md)
