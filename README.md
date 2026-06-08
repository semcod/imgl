# imgl


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-0.7.1-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$2.05-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-2.0h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $2.0516 (2 commits)
- 👤 **Human dev:** ~$200 (2.0h @ $100/h, 30min dedup)

Generated on 2026-06-08 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

Image to Layout — convert screenshots into semantic UI models with OCR text and element bounding boxes.

## Installation

```bash
pip install -e .              # from repo
pip install -e ".[capture]"   # + screen capture (mss)
pip install -e ".[diagnose]"   # numpy for img2nl (install img2nl locally)
pip install -e ".[full]"      # capture + dev (no PyPI vql/img2vql)

# Local siblings (not on PyPI):
pip install -e ~/github/wronai/img2nl[analyze]
pip install -e ~/github/oqlos/vql
pip install -e ~/github/oqlos/vql/packages/img2vql
```

For `uri2vql adopt-imgl`, install imgl in the same venv as uri2vql:

```bash
pip install -e ~/github/semcod/imgl
# or: pip install -e ~/github/oqlos/vql/packages/uri2vql[imgl]
```

System dependency for OCR:

```bash
# Debian/Ubuntu
sudo apt install tesseract-ocr tesseract-ocr-pol

# macOS
brew install tesseract tesseract-lang
```

Development install:

```bash
pip install -e ".[dev]"
```

## Usage

### Python API

```python
from imgl import analyze, scene_to_json

scene = analyze("screen.png", lang="eng+pol")
print(scene_to_json(scene))
```

### CLI

```bash
# Use an existing screenshot (recommended on GNOME/Wayland):
imgl diagnose /tmp/screen.png
imgl vql /tmp/screen.png -o layout.vql.json

# Or capture (needs vql portal on Wayland — mss alone gives black screen):
pip install -e ~/github/oqlos/vql   # portal/grim backends
imgl capture --interactive -o screen.png
imgl diagnose screen.png            # must show worth_analyzing: true

# analyze / export (aborts on blank unless --allow-blank)
imgl analyze /tmp/screen.png --json
imgl analyze screen.png -o screen.imgl.json --lang eng+pol
imgl html screen.png -o screen.html --embed-image
imgl svg screen.png --mode overlay -o screen.svg
imgl svg screen.png --mode wireframe -o screen.svg
imgl vql screen.png -o layout.vql.json --with-grid
```

### Interactive shell (pick action from catalog)

```bash
imgl interact /tmp/screen.png -o layout.vql.json
# numer opcji, NL: "kliknij Save", "mapa", "lista", "quit"
# obraz z numerami jak w shellu:
imgl annotate screen.png --open
imgl interact screen.png --annotate --open
# lepsza lista (filtr szumu OCR):
imgl interact screen.png
# vision LLM (wymaga OPENROUTER_API_KEY + pip install -e ".[llm]"):
imgl interact screen.png --llm --annotate --open
# opcjonalnie wykonaj na pulpicie:
imgl interact /tmp/screen.png --execute   # wymaga xdotool lub ydotool
```

URI DSL (`vql://window/imgl?action=...`):

| action | opis |
|--------|------|
| `analyze` | OCR + layout → VQL JSON (domyślne) |
| `list` | lista elementów interaktywnych |
| `annotate` | PNG ze zrzutu + numerowane ramki |
| `click` | `text=`, `element_id=`, `window=` |
| `type` | `value=`, `label=`, `text=` |

Via `uri2vql` (when installed):

```bash
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&lang=eng'
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&action=list'
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&action=click&text=Save'
# For Polish+English OCR in URI use encoded plus: lang=eng%2Bpol
```

NL → URI (`nlp2uri` / `imgl` built-in):

```bash
# w shellu imgl interact: "kliknij Save", "wpisz test w search", "2", "lista"
```

### HTML / SVG export

```python
from imgl import analyze, scene_to_html, scene_to_svg

scene = analyze("screen.png")
html = scene_to_html(scene, embed_image=True)
svg = scene_to_svg(scene, mode="overlay", background="screen.png")
```

HTML uses absolutely positioned elements with `data-type`, `data-id`, `data-text` attributes
for text-based automation (`button[data-text="Save"]`).

SVG supports `wireframe` (flat debug view) and `overlay` (boxes on top of screenshot).

## Output format

`analyze()` returns a `Scene` with:

- `windows` — detected UI windows/panels (local heuristics or optional `img2vql`)
- `elements` — classified UI elements: `button`, `input`, `label`, `text`, `toolbar`
- `ocr_boxes` — raw OCR word boxes with confidence scores

Example JSON:

```json
{
  "version": "1.0",
  "scene": {"width": 800, "height": 600, "source_image": "screen.png"},
  "windows": [{
    "id": "win-screen",
    "bbox": {"x": 0, "y": 0, "w": 800, "h": 600},
    "title": null,
    "z": 0,
    "elements": [
      {"id": "text-0", "type": "text", "text": "Save", "bbox": {"x": 100, "y": 50, "w": 40, "h": 16}}
    ]
  }],
  "ocr_boxes": [],
  "metadata": {"ocr_backend": "tesseract", "lang": "eng+pol"}
}
```

## Configuration

```python
from imgl import ImglConfig, analyze

scene = analyze("screen.png", config=ImglConfig(
    lang="eng+pol",
    use_img2vql=True,      # use img2vql when installed, else local detect
    detect_inputs=True,
    label_proximity_px=40,
))
```

### VQL export

```python
from imgl import analyze, scene_to_vql, write_vql_program

scene = analyze("screen.png")
program = scene_to_vql(scene, include_grid=True, grid=12)
write_vql_program(scene, "layout.vql.json")
```

Layers: `windows`, `ui_elements` (with OCR text in metadata), `text_regions`, optional `screen_regions`.

### Text-based actions

```python
from imgl import analyze, actions

scene = analyze("screen.png")
ui = actions(scene)

ui.click("button", text="Save")
# {"action": "click", "x": 310, "y": 206, ...}

ui.type_into("alice", label="Username")
# {"action": "type", "x": 245, "y": 99, "text": "alice", ...}
```

CLI:

```bash
imgl find screen.png --type button --text Save --click
imgl find screen.png --label Username --type-into alice
imgl find screen.png --list
```

## Roadmap

- `nlp2uri` phrases for `vql://window/imgl`
- koru desktop bridge for action execution

## License

Licensed under Apache-2.0.
