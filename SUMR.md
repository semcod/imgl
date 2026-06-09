# ImgL - Image to Layout — convert screenshots into semantic UI models with OCR text and element bounding boxes.

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Dependencies](#dependencies)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `imgl`
- **version**: `0.7.2`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(3), app.doql.less, goal.yaml, .env.example, src(24 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: imgl;
  version: 0.7.2;
}

dependencies {
  runtime: "pillow>=10.0, pytesseract>=0.3.10";
  capture: mss>=9.0;
  diagnose: numpy>=1.24;
  llm: "litellm>=1.30, python-dotenv>=1.0";
  web: "fastapi>=0.110, uvicorn[standard]>=0.30";
  full: "imgl[capture,diagnose,dev,llm,web]";
  dev: "pytest>=8.0, goal>=2.1.0, costs>=0.1.20, pfix>=0.1.60";
}

interface[type="api"] {
  type: rest;
  framework: fastapi;
}

interface[type="mcp"] {
  framework: stdio;
  tools: imgl_apply_nl, imgl_run_command, imgl_to_dsl;
}

interface[type="cli"] {
  framework: click;
}
interface[type="cli"] page[name="imgl"] {
  entry: imgl.cli:main;
}

workflow[name="venv"] {
  trigger: manual;
  step-1: run cmd=test -x "$(PY)" || $(PYTHON) -m venv "$(VENV)";
}

workflow[name="install"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install -e .;
}

workflow[name="install-dev"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install -e ".[dev,llm,capture]";
}

workflow[name="install-control"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install "jsonschema>=4.0" "protobuf>=5.0";
  step-2: run cmd=$(PIP) install -e packages/dsl2imgl packages/nlp2imgl packages/rest2imgl packages/cli2imgl;
}

workflow[name="install-full"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install -e ".[web]";
  step-2: run cmd=$(PIP) install "jsonschema>=4.0" "protobuf>=5.0";
}

workflow[name="install-img2nl"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) install img2nl;
}

workflow[name="install-vdisplay"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) install vdisplay;
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m pytest tests packages/dsl2imgl/tests -q;
}

workflow[name="test-imgl"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m pytest tests/test_autodiag.py tests/test_vdisplay_bridge.py tests/test_nlp2imgl_control.py -q;
}

workflow[name="test-dsl2imgl"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m pytest packages/dsl2imgl/tests -q;
}

workflow[name="capture"] {
  trigger: manual;
  step-1: run cmd=test -x "$(PY)" || (echo "Brak $(VENV) — make install-dev" && exit 1);
  step-2: run cmd=$(IMGL) capture --smart -o "$(IMGL_IMAGE)";
}

workflow[name="capture-interactive"] {
  trigger: manual;
  step-1: run cmd=depend target=install-dev;
  step-2: run cmd=rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)";
  step-3: run cmd=IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture -o "$(IMGL_IMAGE)" --verify;
  step-4: run cmd=rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)";
  step-5: run cmd=echo "export IMGL_IMAGE=$(IMGL_IMAGE)";
}

workflow[name="verify-capture"] {
  trigger: manual;
  step-1: run cmd=BEFORE=$$(stat -c %Y "$(IMGL_IMAGE)" 2>/dev/null || echo 0); \;
  step-2: run cmd=$(IMGL) verify "$(IMGL_IMAGE)" --before "$$BEFORE";
}

workflow[name="windows"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) map --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)";
}

workflow[name="doctor"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) doctor --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)";
}

workflow[name="doctor-full"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) doctor --full --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)";
}

workflow[name="execute"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1);
  step-2: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make execute PROMPT='wpisz test w Chat input'" && exit 1);
  step-3: run cmd=$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)";
}

workflow[name="execute-dry"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1);
  step-2: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make execute-dry PROMPT='wpisz test w Chat input'" && exit 1);
  step-3: run cmd=$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --dry-run --format "$(FORMAT)";
}

workflow[name="execute-llm"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1);
  step-2: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make execute-llm PROMPT='wpisz test w Chat input'" && exit 1);
  step-3: run cmd=test -n "$$OPENROUTER_API_KEY" || (echo "Brak OPENROUTER_API_KEY — ustaw klucz OpenRouter" && exit 1);
  step-4: run cmd=$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --llm --format "$(FORMAT)";
}

workflow[name="shot"] {
  trigger: manual;
  step-1: depend target=capture-interactive;
  step-2: depend target=execute;
}

workflow[name="shot-llm"] {
  trigger: manual;
  step-1: depend target=capture-interactive;
  step-2: depend target=execute-llm;
}

workflow[name="proto"] {
  trigger: manual;
  step-1: run cmd=bash packages/dsl2imgl/scripts/generate-proto.sh;
}

workflow[name="serve-rest"] {
  trigger: manual;
  step-1: run cmd=$(VENV)/bin/rest2imgl serve --port $(REST_PORT);
}

workflow[name="serve-web"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m imgl.cli serve --port $(WEB_PORT) --image $(IMGL_IMAGE) --llm --window $(IMGL_WINDOW);
}

workflow[name="demo-key"] {
  trigger: manual;
  step-1: run cmd=$(VENV)/bin/dsl2imgl exec 'KEY ctrl+Return EXECUTE 0';
}

workflow[name="demo-nl"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak $(IMGL_IMAGE) — uruchom: make capture" && exit 1);
  step-2: run cmd=$(VENV)/bin/nlp2imgl apply "wpisz test w Chat input" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW) --dry-run;
}

workflow[name="demo-chat"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak $(IMGL_IMAGE) — uruchom: make capture" && exit 1);
  step-2: run cmd=$(VENV)/bin/nlp2imgl apply "wpisz demo w Chat input" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW) --dry-run;
  step-3: run cmd=$(VENV)/bin/nlp2imgl apply "naciśnij ctrl+enter" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW) --dry-run;
}

tests {
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL;
}

deploy {
  target: makefile;
}

environment[name="local"] {
  runtime: python;
  env_file: .env;
  template_file: .env.example;
  python_version: >=3.10;
  vars: LLM_MODEL, OPENROUTER_API_KEY;
  runtime_llm: OPENROUTER_API_KEY;
}
```

### Source Modules

- `imgl.actions`
- `imgl.autodiag`
- `imgl.capture`
- `imgl.catalog`
- `imgl.catalog_filter`
- `imgl.cli`
- `imgl.config`
- `imgl.coords`
- `imgl.diagnose`
- `imgl.execute`
- `imgl.freshness`
- `imgl.geometry`
- `imgl.interact`
- `imgl.layout`
- `imgl.llm_catalog`
- `imgl.nlp2uri`
- `imgl.paths`
- `imgl.pipeline`
- `imgl.preprocess`
- `imgl.scene_cache`
- `imgl.types`
- `imgl.uri`
- `imgl.vdisplay_bridge`
- `imgl.window_scope`

## Workflows

## Dependencies

### Runtime

```text markpact:deps python
pillow>=10.0
pytesseract>=0.3.10
```

### Development

```text markpact:deps python scope=dev
pytest>=8.0
goal>=2.1.0
costs>=0.1.20
pfix>=0.1.60
```

## Source Map

*Top 5 modules by symbol density — signatures for LLM orientation.*

### `imgl.window_scope` (`imgl/window_scope.py`)

```python
def is_monolithic_scene(scene)  # CC=2, fan=2
def apply_discovered_windows(scene)  # CC=1, fan=3
def discover_windows(scene)  # CC=2, fan=3
def summarize_windows(scene)  # CC=6, fan=7
def format_window_picker(summaries)  # CC=4, fan=4
def get_discovered_window(scene, window_ref)  # CC=10, fan=6 ⚠
def scene_for_window(scene, window)  # CC=4, fan=6
def crop_window_image(image_path, window)  # CC=1, fan=7
def export_window_crop(image_path, window)  # CC=3, fan=7
def default_window_annotated_path(image_path, window_id)  # CC=2, fan=3
def _split_monolithic_window(scene)  # CC=8, fan=12
def _collect_elements(scene)  # CC=2, fan=1
def _detect_layout_mode(elements, window_bbox)  # CC=12, fan=6 ⚠
def _split_side_by_side(window_bbox, elements)  # CC=2, fan=3
def _split_stacked(window_bbox, elements)  # CC=6, fan=8
def _image_gutter_candidates(image_path, window_bbox)  # CC=14, fan=11 ⚠
def _element_gap_gutters(window_bbox, elements)  # CC=6, fan=8
def _regions_from_balanced_gutters(window_bbox, elements, candidates)  # CC=18, fan=11 ⚠
def _split_by_element_y_gaps(window_bbox, elements)  # CC=10, fan=9 ⚠
def _best_vertical_split(elements, window_bbox)  # CC=12, fan=7 ⚠
def _region_id_for_boxes(index, count, layout)  # CC=7, fan=0
def _guess_window_title(window, ocr_boxes)  # CC=6, fan=5
def _shift_elements(elements, origin)  # CC=2, fan=5
def _shift_ocr_boxes(boxes, origin)  # CC=2, fan=3
def _safe_filename(value)  # CC=6, fan=4
class WindowSummary:  # One discoverable window region with stats for the picker UI.
    def label()  # CC=2
    def bbox()  # CC=1
```

### `imgl.autodiag` (`imgl/autodiag.py`)

```python
def img2nl_root()  # CC=1, fan=4
def img2nl_available()  # CC=1, fan=2
def diagnose_capture(image_path)  # CC=16, fan=16 ⚠
def build_operation_step(result)  # CC=19, fan=9 ⚠
def _compact_result(result)  # CC=6, fan=3
def build_execute_report()  # CC=5, fan=5
def pick_output_format(payload, requested)  # CC=7, fan=2
def render_report(payload, fmt)  # CC=3, fan=4
def _flag_enabled()  # CC=3, fan=3
def should_block_blank_capture(capture)  # CC=2, fan=2
def should_block_stale_capture(capture)  # CC=3, fan=2
def diagnostics_enabled()  # CC=1, fan=1
def _render_markdown(report)  # CC=24, fan=7 ⚠
def _overall_verdict(capture, operation)  # CC=10, fan=1 ⚠
def _actionable_hints(report)  # CC=12, fan=3 ⚠
def _compact_features(features)  # CC=6, fan=1
def _scene_class(diag)  # CC=2, fan=2
def _parse_coords(message)  # CC=2, fan=3
def _coords_from_action(action)  # CC=3, fan=1
def _parse_typed_text(message)  # CC=2, fan=2
def _parse_keys(message)  # CC=2, fan=3
```

### `imgl.actions` (`imgl/actions.py`)

```python
def actions(scene)  # CC=1, fan=1
def _format_query(element_type)  # CC=5, fan=2
def _text_matches(value, query)  # CC=3, fan=1
def _iter_elements(scene)  # CC=9, fan=2
def _window_matches(window, query)  # CC=4, fan=1
def _find_label_for_input(scene, input_element, window)  # CC=6, fan=5
class ActionTarget:  # A resolved UI element that can be clicked or typed into.
    def center()  # CC=1
    def click_coords()  # CC=1
    def to_click_action()  # CC=2
class TypeAction:  # Type text into an input field.
    def coords()  # CC=1
    def to_dict()  # CC=2
class SceneActions:  # Find and interact with elements in a Scene.
    def find(element_type)  # CC=21 ⚠
    def find_one(element_type)  # CC=2
    def click(element_type)  # CC=2
    def type_into(value)  # CC=5
    def list_actions()  # CC=5
class ElementNotFoundError:  # Raised when no element matches the query.
```

### `imgl.llm_catalog` (`imgl/llm_catalog.py`)

```python
def _env_file_candidates()  # CC=1, fan=3
def _load_env_files()  # CC=12, fan=9 ⚠
def llm_available()  # CC=1, fan=4
def llm_dependencies_ok()  # CC=2, fan=0
def refine_catalog_with_llm(scene)  # CC=14, fan=12 ⚠
def _heuristic_fallback(scene)  # CC=2, fan=2
def _short_error(exc)  # CC=3, fan=3
def _call_vision_llm(image_path)  # CC=4, fan=6
def _parse_json_payload(content)  # CC=3, fan=3
def _image_to_base64(image_path)  # CC=3, fan=12
def _llm_json_to_options(payload)  # CC=13, fan=13 ⚠
def _snap_options_to_scene(options, scene)  # CC=8, fan=6
def _merge_heuristic_inputs(llm_options, scene)  # CC=4, fan=5
def _overlaps_catalog(option, others)  # CC=4, fan=3
def _renumber_options(options)  # CC=2, fan=3
def _best_label_match(label, candidates)  # CC=13, fan=5 ⚠
```

### `imgl.capture` (`imgl/capture.py`)

```python
def default_capture_path(out)  # CC=2, fan=6
def _is_wayland()  # CC=3, fan=3
def capture_screen(out)  # CC=13, fan=10 ⚠
def _try_vql_capture(path)  # CC=8, fan=7
def _native_backends()  # CC=3, fan=4
def _run_command(cmd, path)  # CC=3, fan=4
def _capture_with_grim(path)  # CC=2, fan=3
def _capture_with_gnome_screenshot(path)  # CC=2, fan=3
def _capture_with_scrot(path)  # CC=2, fan=3
def _capture_with_portal(path)  # CC=3, fan=5
def _capture_with_mss(path)  # CC=1, fan=8
def _is_blank_image(path)  # CC=6, fan=13
def capture_status_message(path)  # CC=2, fan=1
class CaptureError:  # Raised when screen capture fails.
class BlankCaptureError:  # Raised when capture succeeded but image is empty/black.
```

## Call Graph

*302 nodes · 393 edges · 57 modules · CC̄=5.3*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `create_app` *(in imgl.web.app)* | 4 | 2 | 107 | **109** |
| `print` *(in scripts.imgl-verify-capture)* | 0 | 95 | 0 | **95** |
| `main` *(in imgl.cli)* | 44 ⚠ | 0 | 94 | **94** |
| `run_interactive_shell` *(in imgl.interact)* | 43 ⚠ | 1 | 87 | **88** |
| `build_parser` *(in imgl.cli)* | 1 | 1 | 73 | **74** |
| `_set_body` *(in packages.dsl2imgl.src.dsl2imgl.pb_codec)* | 31 ⚠ | 1 | 73 | **74** |
| `parse_line` *(in packages.dsl2imgl.src.dsl2imgl.grammar)* | 44 ⚠ | 2 | 46 | **48** |
| `diagnose_capture` *(in imgl.autodiag)* | 16 ⚠ | 4 | 41 | **45** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/imgl
# generated in 0.13s
# nodes: 302 | edges: 393 | modules: 57
# CC̄=5.3

HUBS[20]:
  imgl.web.app.create_app
    CC=4  in:2  out:107  total:109
  scripts.imgl-verify-capture.print
    CC=0  in:95  out:0  total:95
  imgl.cli.main
    CC=44  in:0  out:94  total:94
  imgl.interact.run_interactive_shell
    CC=43  in:1  out:87  total:88
  imgl.cli.build_parser
    CC=1  in:1  out:73  total:74
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_body
    CC=31  in:1  out:73  total:74
  packages.dsl2imgl.src.dsl2imgl.grammar.parse_line
    CC=44  in:2  out:46  total:48
  imgl.autodiag.diagnose_capture
    CC=16  in:4  out:41  total:45
  imgl.cli._run_image_command
    CC=19  in:1  out:43  total:44
  imgl.detect.local._detect_buttons
    CC=24  in:1  out:41  total:42
  imgl.nlp2uri.prompt_to_imgl_uri
    CC=28  in:4  out:37  total:41
  imgl.autodiag._render_markdown
    CC=24  in:1  out:35  total:36
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch
    CC=10  in:14  out:21  total:35
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_execute
    CC=14  in:0  out:35  total:35
  imgl.autodiag.build_operation_step
    CC=19  in:1  out:33  total:34
  imgl.vdisplay_bridge.correlate_windows
    CC=18  in:1  out:32  total:33
  imgl.vdisplay_bridge.build_window_control_report
    CC=19  in:1  out:32  total:33
  imgl.detect.local._detect_panels_simple
    CC=23  in:1  out:31  total:32
  imgl.coords.scale_scene_to_screen
    CC=6  in:1  out:29  total:30
  imgl.classify.gui_heuristics.classify_scene_elements
    CC=27  in:1  out:29  total:30

MODULES:
  examples.scripts.demo-nlp2uri  [1 funcs]
    main  CC=7  out:25
  imgl.actions  [10 funcs]
    click  CC=2  out:4
    find  CC=21  out:18
    list_actions  CC=5  out:9
    type_into  CC=5  out:7
    _find_label_for_input  CC=6  out:5
    _format_query  CC=5  out:5
    _iter_elements  CC=9  out:2
    _text_matches  CC=3  out:2
    _window_matches  CC=4  out:3
    actions  CC=1  out:1
  imgl.autodiag  [13 funcs]
    _actionable_hints  CC=12  out:17
    _compact_result  CC=6  out:4
    _flag_enabled  CC=3  out:3
    _overall_verdict  CC=10  out:8
    _render_markdown  CC=24  out:35
    build_execute_report  CC=5  out:15
    build_operation_step  CC=19  out:33
    diagnose_capture  CC=16  out:41
    diagnostics_enabled  CC=1  out:1
    pick_output_format  CC=7  out:4
  imgl.capture  [12 funcs]
    _capture_with_gnome_screenshot  CC=2  out:3
    _capture_with_grim  CC=2  out:3
    _capture_with_mss  CC=1  out:8
    _capture_with_scrot  CC=2  out:3
    _is_blank_image  CC=6  out:13
    _is_wayland  CC=3  out:4
    _native_backends  CC=3  out:4
    _run_command  CC=3  out:4
    _try_vql_capture  CC=8  out:9
    capture_screen  CC=13  out:15
  imgl.catalog  [8 funcs]
    _element_option  CC=13  out:19
    _find_window  CC=2  out:1
    _infer_input_label  CC=13  out:0
    _iter_interactive_elements  CC=9  out:2
    _truncate  CC=2  out:3
    _window_option  CC=2  out:5
    build_interactive_catalog  CC=12  out:11
    format_catalog_table  CC=8  out:10
  imgl.catalog_filter  [6 funcs]
    _element_score  CC=9  out:5
    _keep_element  CC=17  out:13
    _renumber  CC=2  out:4
    _replace_index_in_uri  CC=1  out:0
    _window_score  CC=5  out:1
    filter_catalog  CC=8  out:7
  imgl.classify.gui_heuristics  [9 funcs]
    _build_inputs  CC=7  out:10
    _label_candidates  CC=5  out:3
    _match_ocr_to_bbox  CC=5  out:3
    _nearest_label  CC=7  out:4
    _normalize_confidence  CC=2  out:0
    _ocr_inside_frame  CC=4  out:1
    _text_or_label  CC=7  out:5
    _word_count  CC=1  out:2
    classify_scene_elements  CC=27  out:29
  imgl.cli  [7 funcs]
    _add_common_args  CC=1  out:5
    _apply_config_overrides  CC=2  out:1
    _check_blank_before_analyze  CC=5  out:7
    _run_image_command  CC=19  out:43
    _write_output  CC=2  out:3
    build_parser  CC=1  out:73
    main  CC=44  out:94
  imgl.coords  [1 funcs]
    scale_scene_to_screen  CC=6  out:29
  imgl.detect.img2vql_bridge  [4 funcs]
    _from_img2vql_dict  CC=1  out:7
    detect_ui_merged  CC=4  out:2
    detect_with_img2vql  CC=4  out:5
    img2vql_available  CC=2  out:0
  imgl.detect.local  [8 funcs]
    _avg_color  CC=5  out:8
    _dedupe  CC=8  out:10
    _detect_buttons  CC=24  out:41
    _detect_panels_simple  CC=23  out:31
    _detect_titlebar  CC=5  out:11
    _flood_rects  CC=14  out:13
    _iou_xyxy  CC=3  out:5
    detect_ui_elements  CC=4  out:7
  imgl.detect.rectangles  [5 funcs]
    _column_has_edge  CC=2  out:3
    _find_rectangular_frames  CC=11  out:8
    _looks_like_frame  CC=6  out:4
    _row_has_edge  CC=2  out:3
    detect_input_frames  CC=14  out:22
  imgl.diagnose  [10 funcs]
    _diagnose_fallback  CC=8  out:14
    _diagnose_pil_fallback  CC=7  out:10
    _diagnose_with_img2nl  CC=2  out:5
    _has_ui_signals  CC=7  out:11
    _recommendation  CC=10  out:9
    _scene_class  CC=2  out:6
    content_summary  CC=6  out:6
    diagnose_content  CC=3  out:7
    img2nl_available  CC=2  out:0
    worth_analyzing  CC=6  out:5
  imgl.execute  [3 funcs]
    _normalize_keys  CC=9  out:12
    execute_action  CC=9  out:19
    execute_keys  CC=5  out:8
  imgl.export._escape  [2 funcs]
    escape_html  CC=1  out:1
    escape_xml  CC=1  out:5
  imgl.export.annotate_export  [11 funcs]
    _badge_size  CC=1  out:4
    _catalog_relative_to_window  CC=2  out:2
    _draw_number_badge  CC=1  out:3
    _load_fonts  CC=2  out:8
    _text_size  CC=2  out:3
    default_annotated_path  CC=3  out:3
    open_image  CC=4  out:5
    scene_to_annotated_image  CC=8  out:25
    write_annotated_image  CC=1  out:5
    write_annotated_images_per_window  CC=5  out:6
  imgl.export.html_export  [7 funcs]
    _background_layer  CC=3  out:1
    _base_css  CC=1  out:0
    _bbox_style  CC=1  out:0
    _default_title  CC=4  out:1
    _render_element  CC=8  out:13
    _render_window  CC=3  out:5
    scene_to_html  CC=4  out:9
  imgl.export.json_export  [2 funcs]
    scene_from_json  CC=2  out:3
    scene_to_json  CC=1  out:2
  imgl.export.svg_export  [7 funcs]
    _background_rect  CC=4  out:1
    _default_title  CC=4  out:1
    _element_css_class  CC=1  out:1
    _render_element_svg  CC=4  out:7
    _render_window_svg  CC=3  out:5
    _svg_css  CC=1  out:0
    scene_to_svg  CC=4  out:9
  imgl.export.vql_adapter  [10 funcs]
    _bbox_norm  CC=5  out:5
    _element_to_object  CC=4  out:2
    _grid_layer  CC=4  out:2
    _location_label  CC=9  out:2
    _object_from_bbox  CC=2  out:11
    _ocr_to_object  CC=2  out:2
    _window_to_object  CC=2  out:1
    scene_to_vql  CC=16  out:27
    scene_to_vql_json  CC=1  out:2
    write_vql_program  CC=1  out:3
  imgl.freshness  [9 funcs]
    capture_sidecar_path  CC=1  out:1
    clear_vql_cache  CC=3  out:5
    image_freshness  CC=5  out:21
    is_valid_png  CC=3  out:6
    mark_capture_fresh  CC=2  out:7
    max_image_age_seconds  CC=4  out:4
    sync_vql_cache_with_image  CC=5  out:7
    verify_capture_updated  CC=4  out:10
    vql_cache_paths  CC=1  out:2
  imgl.geometry  [4 funcs]
    bbox_distance  CC=1  out:0
    bbox_from_xyxy  CC=1  out:1
    center_in  CC=2  out:1
    iou  CC=3  out:7
  imgl.interact  [8 funcs]
    _annotate_catalog  CC=6  out:8
    _build_session_catalog  CC=2  out:1
    _export_window_previews  CC=4  out:6
    _handle_window_phase_prompt  CC=9  out:21
    _print_catalog_banner  CC=8  out:10
    _select_window  CC=6  out:6
    resolve_imgl_uri  CC=13  out:19
    run_interactive_shell  CC=43  out:87
  imgl.layout  [6 funcs]
    _best_titlebar_for_window  CC=5  out:3
    _overlaps_top  CC=2  out:2
    assign_ocr_to_windows  CC=4  out:3
    build_windows  CC=6  out:7
    extract_window_titles  CC=10  out:4
    find_containing_window  CC=4  out:2
  imgl.llm_catalog  [15 funcs]
    _best_label_match  CC=13  out:10
    _call_vision_llm  CC=4  out:6
    _env_file_candidates  CC=1  out:3
    _heuristic_fallback  CC=2  out:2
    _image_to_base64  CC=3  out:13
    _llm_json_to_options  CC=13  out:22
    _load_env_files  CC=12  out:17
    _merge_heuristic_inputs  CC=4  out:5
    _overlaps_catalog  CC=4  out:5
    _parse_json_payload  CC=3  out:4
  imgl.nlp2uri  [4 funcs]
    _delegate_vql_nlp2uri  CC=5  out:6
    _find_catalog_input  CC=9  out:4
    _match_catalog_action  CC=8  out:4
    prompt_to_imgl_uri  CC=28  out:37
  imgl.ocr  [1 funcs]
    get_ocr_backend  CC=2  out:2
  imgl.ocr.lang  [2 funcs]
    normalize_ocr_lang  CC=3  out:2
    ocr_lang_attempts  CC=6  out:7
  imgl.ocr.tesseract  [1 funcs]
    run  CC=13  out:17
  imgl.paths  [2 funcs]
    resolve_image_path  CC=5  out:11
    resolve_image_path_optional  CC=3  out:2
  imgl.pipeline  [3 funcs]
    _content_metadata  CC=1  out:6
    _count_roles  CC=4  out:2
    analyze  CC=11  out:21
  imgl.preprocess  [2 funcs]
    load_image  CC=2  out:8
    preprocess  CC=3  out:8
  imgl.scene_cache  [4 funcs]
    load_cached_scene  CC=5  out:10
    load_or_analyze  CC=5  out:7
    save_scene_cache  CC=1  out:3
    scene_cache_path  CC=2  out:3
  imgl.uri  [7 funcs]
    _imgl_uri  CC=5  out:3
    uri_for_imgl_action  CC=1  out:1
    uri_for_imgl_analyze  CC=2  out:1
    uri_for_imgl_annotate  CC=2  out:1
    uri_for_imgl_click  CC=5  out:1
    uri_for_imgl_list  CC=1  out:1
    uri_for_imgl_type  CC=5  out:1
  imgl.vdisplay_bridge  [10 funcs]
    _norm  CC=1  out:2
    build_window_control_report  CC=19  out:32
    correlate_windows  CC=18  out:32
    default_display  CC=2  out:3
    diagnose_os_display  CC=4  out:5
    find_os_window  CC=6  out:5
    list_os_monitors  CC=3  out:3
    list_os_windows  CC=3  out:3
    list_vision_windows  CC=4  out:11
    vdisplay_missing_message  CC=2  out:4
  imgl.web.agent  [2 funcs]
    _parse_agent_json  CC=6  out:7
    pick_agent_action  CC=20  out:23
  imgl.web.app  [1 funcs]
    create_app  CC=4  out:107
  imgl.web.session  [6 funcs]
    _refresh_annotated_png  CC=3  out:6
    analyze  CC=1  out:6
    capture  CC=1  out:4
    refresh_catalog  CC=2  out:2
    resolve_prompt  CC=2  out:3
    select_window  CC=4  out:3
  imgl.web.thumbs  [2 funcs]
    _clamp_box  CC=3  out:6
    crop_bbox_png  CC=2  out:15
  imgl.window_scope  [23 funcs]
    _best_vertical_split  CC=12  out:10
    _collect_elements  CC=2  out:2
    _detect_layout_mode  CC=12  out:16
    _element_gap_gutters  CC=6  out:9
    _guess_window_title  CC=6  out:6
    _image_gutter_candidates  CC=14  out:19
    _regions_from_balanced_gutters  CC=18  out:17
    _safe_filename  CC=6  out:5
    _shift_elements  CC=2  out:5
    _shift_ocr_boxes  CC=2  out:3
  packages.cli2imgl.src.cli2imgl.cli  [1 funcs]
    main  CC=6  out:14
  packages.dsl2imgl.src.dsl2imgl.bus  [5 funcs]
    _run_handler  CC=2  out:7
    dispatch  CC=10  out:21
    dispatch_json  CC=1  out:2
    execute_dsl  CC=4  out:6
    execute_dsl_line  CC=1  out:1
  packages.dsl2imgl.src.dsl2imgl.codec  [7 funcs]
    envelope_from_bytes  CC=1  out:2
    envelope_from_json  CC=2  out:5
    envelope_to_bytes  CC=1  out:2
    envelope_to_json  CC=1  out:3
    parse_text  CC=2  out:2
    roundtrip_text  CC=1  out:4
    validate_payload  CC=2  out:6
  packages.dsl2imgl.src.dsl2imgl.events  [2 funcs]
    _append_jsonl  CC=3  out:27
    _append_pb  CC=3  out:27
  packages.dsl2imgl.src.dsl2imgl.grammar  [4 funcs]
    parse_line  CC=44  out:46
    pick_flag  CC=3  out:2
    split_command  CC=4  out:4
    to_text  CC=10  out:20
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime  [7 funcs]
    _build_interact_session  CC=4  out:12
    _run_prompt_act  CC=8  out:15
    handle_actions  CC=4  out:11
    handle_analyze  CC=4  out:10
    handle_capture  CC=3  out:9
    handle_execute  CC=14  out:35
    handle_resolve  CC=7  out:14
  packages.dsl2imgl.src.dsl2imgl.pb_codec  [9 funcs]
    _set_body  CC=31  out:73
    decode_protobuf  CC=1  out:3
    decode_protobuf_to_text  CC=1  out:2
    dict_to_envelope  CC=1  out:5
    encode_protobuf  CC=1  out:2
    encode_result_protobuf  CC=1  out:2
    encode_text_to_protobuf  CC=2  out:3
    envelope_to_dict  CC=42  out:6
    result_to_pb  CC=3  out:3
  packages.dsl2imgl.src.dsl2imgl.schema_registry  [4 funcs]
    _load_schemas  CC=4  out:11
    all_verbs  CC=1  out:3
    schema_for_verb  CC=2  out:4
    validate_schemas  CC=3  out:6
  packages.mcp2imgl.src.mcp2imgl.cli  [1 funcs]
    main  CC=2  out:5
  packages.mcp2imgl.src.mcp2imgl.server  [1 funcs]
    run_stdio  CC=2  out:12
  packages.nlp2imgl.src.nlp2imgl.control  [5 funcs]
    _result_to_dict  CC=4  out:13
    apply_nl_with_diag  CC=17  out:16
    default_image_path  CC=3  out:5
    default_window  CC=3  out:2
    doctor_capture  CC=2  out:4
  packages.nlp2imgl.src.nlp2imgl.to_dsl  [3 funcs]
    apply_nl  CC=5  out:7
    to_dsl  CC=15  out:19
    use_llm_enabled  CC=4  out:6
  packages.rest2imgl.src.rest2imgl.cli  [1 funcs]
    main  CC=2  out:8
  packages.uri2imgl.src.uri2imgl.cli  [1 funcs]
    main  CC=4  out:15
  packages.uri2imgl.src.uri2imgl.decode  [1 funcs]
    uri_to_dsl  CC=18  out:16
  scripts.imgl-capture  [1 funcs]
    mark_capture_fresh  CC=0  out:0
  scripts.imgl-verify-capture  [1 funcs]
    print  CC=0  out:0

EDGES:
  packages.rest2imgl.src.rest2imgl.cli.main → imgl.web.app.create_app
  packages.cli2imgl.src.cli2imgl.cli.main → scripts.imgl-verify-capture.print
  packages.cli2imgl.src.cli2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.cli2imgl.src.cli2imgl.cli.main → packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.mcp2imgl.src.mcp2imgl.cli.main → packages.mcp2imgl.src.mcp2imgl.server.run_stdio
  packages.mcp2imgl.src.mcp2imgl.server.run_stdio → packages.nlp2imgl.src.nlp2imgl.to_dsl.to_dsl
  packages.mcp2imgl.src.mcp2imgl.server.run_stdio → packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.bus._run_handler
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.grammar.to_text
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.bus.execute_dsl_line → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.dsl2imgl.src.dsl2imgl.bus.execute_dsl → packages.dsl2imgl.src.dsl2imgl.bus.execute_dsl_line
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch_json → packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_json
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch_json → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb → packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl → packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb
  packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope → packages.dsl2imgl.src.dsl2imgl.pb_codec._set_body
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
  packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.envelope_to_dict
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_text_to_protobuf → packages.dsl2imgl.src.dsl2imgl.grammar.parse_line
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_text_to_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf
  packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf_to_text → packages.dsl2imgl.src.dsl2imgl.grammar.to_text
  packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf_to_text → packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_result_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb
  packages.dsl2imgl.src.dsl2imgl.schema_registry.schema_for_verb → packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas
  packages.dsl2imgl.src.dsl2imgl.schema_registry.all_verbs → packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas
  packages.dsl2imgl.src.dsl2imgl.schema_registry.validate_schemas → packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas
  packages.dsl2imgl.src.dsl2imgl.codec.validate_payload → packages.dsl2imgl.src.dsl2imgl.schema_registry.schema_for_verb
  packages.dsl2imgl.src.dsl2imgl.codec.parse_text → packages.dsl2imgl.src.dsl2imgl.grammar.parse_line
  packages.dsl2imgl.src.dsl2imgl.codec.parse_text → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_bytes → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_bytes → packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes → packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_json → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_json → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.codec.parse_text
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.grammar.to_text
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_bytes
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.scene_cache.load_or_analyze
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.window_scope.apply_discovered_windows
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.interact._build_session_catalog
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.window_scope.summarize_windows
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._run_prompt_act → imgl.nlp2uri.prompt_to_imgl_uri
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Api (2)

**`API Integration Tests`**
- `GET /health` → `200`
- `GET /api/v1/status` → `200`
- `POST /api/v1/test` → `201`
- assert `status == ok`
- assert `response_time < 1000`

**`Auto-generated API Smoke Tests`**
- assert `_status < 500`
- assert `_status >= 200`
- detectors: FastAPIDetector, TestEndpointDetector

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/imgl
# generated in 0.13s
# nodes: 302 | edges: 393 | modules: 57
# CC̄=5.3

HUBS[20]:
  imgl.web.app.create_app
    CC=4  in:2  out:107  total:109
  scripts.imgl-verify-capture.print
    CC=0  in:95  out:0  total:95
  imgl.cli.main
    CC=44  in:0  out:94  total:94
  imgl.interact.run_interactive_shell
    CC=43  in:1  out:87  total:88
  imgl.cli.build_parser
    CC=1  in:1  out:73  total:74
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_body
    CC=31  in:1  out:73  total:74
  packages.dsl2imgl.src.dsl2imgl.grammar.parse_line
    CC=44  in:2  out:46  total:48
  imgl.autodiag.diagnose_capture
    CC=16  in:4  out:41  total:45
  imgl.cli._run_image_command
    CC=19  in:1  out:43  total:44
  imgl.detect.local._detect_buttons
    CC=24  in:1  out:41  total:42
  imgl.nlp2uri.prompt_to_imgl_uri
    CC=28  in:4  out:37  total:41
  imgl.autodiag._render_markdown
    CC=24  in:1  out:35  total:36
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch
    CC=10  in:14  out:21  total:35
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_execute
    CC=14  in:0  out:35  total:35
  imgl.autodiag.build_operation_step
    CC=19  in:1  out:33  total:34
  imgl.vdisplay_bridge.correlate_windows
    CC=18  in:1  out:32  total:33
  imgl.vdisplay_bridge.build_window_control_report
    CC=19  in:1  out:32  total:33
  imgl.detect.local._detect_panels_simple
    CC=23  in:1  out:31  total:32
  imgl.coords.scale_scene_to_screen
    CC=6  in:1  out:29  total:30
  imgl.classify.gui_heuristics.classify_scene_elements
    CC=27  in:1  out:29  total:30

MODULES:
  examples.scripts.demo-nlp2uri  [1 funcs]
    main  CC=7  out:25
  imgl.actions  [10 funcs]
    click  CC=2  out:4
    find  CC=21  out:18
    list_actions  CC=5  out:9
    type_into  CC=5  out:7
    _find_label_for_input  CC=6  out:5
    _format_query  CC=5  out:5
    _iter_elements  CC=9  out:2
    _text_matches  CC=3  out:2
    _window_matches  CC=4  out:3
    actions  CC=1  out:1
  imgl.autodiag  [13 funcs]
    _actionable_hints  CC=12  out:17
    _compact_result  CC=6  out:4
    _flag_enabled  CC=3  out:3
    _overall_verdict  CC=10  out:8
    _render_markdown  CC=24  out:35
    build_execute_report  CC=5  out:15
    build_operation_step  CC=19  out:33
    diagnose_capture  CC=16  out:41
    diagnostics_enabled  CC=1  out:1
    pick_output_format  CC=7  out:4
  imgl.capture  [12 funcs]
    _capture_with_gnome_screenshot  CC=2  out:3
    _capture_with_grim  CC=2  out:3
    _capture_with_mss  CC=1  out:8
    _capture_with_scrot  CC=2  out:3
    _is_blank_image  CC=6  out:13
    _is_wayland  CC=3  out:4
    _native_backends  CC=3  out:4
    _run_command  CC=3  out:4
    _try_vql_capture  CC=8  out:9
    capture_screen  CC=13  out:15
  imgl.catalog  [8 funcs]
    _element_option  CC=13  out:19
    _find_window  CC=2  out:1
    _infer_input_label  CC=13  out:0
    _iter_interactive_elements  CC=9  out:2
    _truncate  CC=2  out:3
    _window_option  CC=2  out:5
    build_interactive_catalog  CC=12  out:11
    format_catalog_table  CC=8  out:10
  imgl.catalog_filter  [6 funcs]
    _element_score  CC=9  out:5
    _keep_element  CC=17  out:13
    _renumber  CC=2  out:4
    _replace_index_in_uri  CC=1  out:0
    _window_score  CC=5  out:1
    filter_catalog  CC=8  out:7
  imgl.classify.gui_heuristics  [9 funcs]
    _build_inputs  CC=7  out:10
    _label_candidates  CC=5  out:3
    _match_ocr_to_bbox  CC=5  out:3
    _nearest_label  CC=7  out:4
    _normalize_confidence  CC=2  out:0
    _ocr_inside_frame  CC=4  out:1
    _text_or_label  CC=7  out:5
    _word_count  CC=1  out:2
    classify_scene_elements  CC=27  out:29
  imgl.cli  [7 funcs]
    _add_common_args  CC=1  out:5
    _apply_config_overrides  CC=2  out:1
    _check_blank_before_analyze  CC=5  out:7
    _run_image_command  CC=19  out:43
    _write_output  CC=2  out:3
    build_parser  CC=1  out:73
    main  CC=44  out:94
  imgl.coords  [1 funcs]
    scale_scene_to_screen  CC=6  out:29
  imgl.detect.img2vql_bridge  [4 funcs]
    _from_img2vql_dict  CC=1  out:7
    detect_ui_merged  CC=4  out:2
    detect_with_img2vql  CC=4  out:5
    img2vql_available  CC=2  out:0
  imgl.detect.local  [8 funcs]
    _avg_color  CC=5  out:8
    _dedupe  CC=8  out:10
    _detect_buttons  CC=24  out:41
    _detect_panels_simple  CC=23  out:31
    _detect_titlebar  CC=5  out:11
    _flood_rects  CC=14  out:13
    _iou_xyxy  CC=3  out:5
    detect_ui_elements  CC=4  out:7
  imgl.detect.rectangles  [5 funcs]
    _column_has_edge  CC=2  out:3
    _find_rectangular_frames  CC=11  out:8
    _looks_like_frame  CC=6  out:4
    _row_has_edge  CC=2  out:3
    detect_input_frames  CC=14  out:22
  imgl.diagnose  [10 funcs]
    _diagnose_fallback  CC=8  out:14
    _diagnose_pil_fallback  CC=7  out:10
    _diagnose_with_img2nl  CC=2  out:5
    _has_ui_signals  CC=7  out:11
    _recommendation  CC=10  out:9
    _scene_class  CC=2  out:6
    content_summary  CC=6  out:6
    diagnose_content  CC=3  out:7
    img2nl_available  CC=2  out:0
    worth_analyzing  CC=6  out:5
  imgl.execute  [3 funcs]
    _normalize_keys  CC=9  out:12
    execute_action  CC=9  out:19
    execute_keys  CC=5  out:8
  imgl.export._escape  [2 funcs]
    escape_html  CC=1  out:1
    escape_xml  CC=1  out:5
  imgl.export.annotate_export  [11 funcs]
    _badge_size  CC=1  out:4
    _catalog_relative_to_window  CC=2  out:2
    _draw_number_badge  CC=1  out:3
    _load_fonts  CC=2  out:8
    _text_size  CC=2  out:3
    default_annotated_path  CC=3  out:3
    open_image  CC=4  out:5
    scene_to_annotated_image  CC=8  out:25
    write_annotated_image  CC=1  out:5
    write_annotated_images_per_window  CC=5  out:6
  imgl.export.html_export  [7 funcs]
    _background_layer  CC=3  out:1
    _base_css  CC=1  out:0
    _bbox_style  CC=1  out:0
    _default_title  CC=4  out:1
    _render_element  CC=8  out:13
    _render_window  CC=3  out:5
    scene_to_html  CC=4  out:9
  imgl.export.json_export  [2 funcs]
    scene_from_json  CC=2  out:3
    scene_to_json  CC=1  out:2
  imgl.export.svg_export  [7 funcs]
    _background_rect  CC=4  out:1
    _default_title  CC=4  out:1
    _element_css_class  CC=1  out:1
    _render_element_svg  CC=4  out:7
    _render_window_svg  CC=3  out:5
    _svg_css  CC=1  out:0
    scene_to_svg  CC=4  out:9
  imgl.export.vql_adapter  [10 funcs]
    _bbox_norm  CC=5  out:5
    _element_to_object  CC=4  out:2
    _grid_layer  CC=4  out:2
    _location_label  CC=9  out:2
    _object_from_bbox  CC=2  out:11
    _ocr_to_object  CC=2  out:2
    _window_to_object  CC=2  out:1
    scene_to_vql  CC=16  out:27
    scene_to_vql_json  CC=1  out:2
    write_vql_program  CC=1  out:3
  imgl.freshness  [9 funcs]
    capture_sidecar_path  CC=1  out:1
    clear_vql_cache  CC=3  out:5
    image_freshness  CC=5  out:21
    is_valid_png  CC=3  out:6
    mark_capture_fresh  CC=2  out:7
    max_image_age_seconds  CC=4  out:4
    sync_vql_cache_with_image  CC=5  out:7
    verify_capture_updated  CC=4  out:10
    vql_cache_paths  CC=1  out:2
  imgl.geometry  [4 funcs]
    bbox_distance  CC=1  out:0
    bbox_from_xyxy  CC=1  out:1
    center_in  CC=2  out:1
    iou  CC=3  out:7
  imgl.interact  [8 funcs]
    _annotate_catalog  CC=6  out:8
    _build_session_catalog  CC=2  out:1
    _export_window_previews  CC=4  out:6
    _handle_window_phase_prompt  CC=9  out:21
    _print_catalog_banner  CC=8  out:10
    _select_window  CC=6  out:6
    resolve_imgl_uri  CC=13  out:19
    run_interactive_shell  CC=43  out:87
  imgl.layout  [6 funcs]
    _best_titlebar_for_window  CC=5  out:3
    _overlaps_top  CC=2  out:2
    assign_ocr_to_windows  CC=4  out:3
    build_windows  CC=6  out:7
    extract_window_titles  CC=10  out:4
    find_containing_window  CC=4  out:2
  imgl.llm_catalog  [15 funcs]
    _best_label_match  CC=13  out:10
    _call_vision_llm  CC=4  out:6
    _env_file_candidates  CC=1  out:3
    _heuristic_fallback  CC=2  out:2
    _image_to_base64  CC=3  out:13
    _llm_json_to_options  CC=13  out:22
    _load_env_files  CC=12  out:17
    _merge_heuristic_inputs  CC=4  out:5
    _overlaps_catalog  CC=4  out:5
    _parse_json_payload  CC=3  out:4
  imgl.nlp2uri  [4 funcs]
    _delegate_vql_nlp2uri  CC=5  out:6
    _find_catalog_input  CC=9  out:4
    _match_catalog_action  CC=8  out:4
    prompt_to_imgl_uri  CC=28  out:37
  imgl.ocr  [1 funcs]
    get_ocr_backend  CC=2  out:2
  imgl.ocr.lang  [2 funcs]
    normalize_ocr_lang  CC=3  out:2
    ocr_lang_attempts  CC=6  out:7
  imgl.ocr.tesseract  [1 funcs]
    run  CC=13  out:17
  imgl.paths  [2 funcs]
    resolve_image_path  CC=5  out:11
    resolve_image_path_optional  CC=3  out:2
  imgl.pipeline  [3 funcs]
    _content_metadata  CC=1  out:6
    _count_roles  CC=4  out:2
    analyze  CC=11  out:21
  imgl.preprocess  [2 funcs]
    load_image  CC=2  out:8
    preprocess  CC=3  out:8
  imgl.scene_cache  [4 funcs]
    load_cached_scene  CC=5  out:10
    load_or_analyze  CC=5  out:7
    save_scene_cache  CC=1  out:3
    scene_cache_path  CC=2  out:3
  imgl.uri  [7 funcs]
    _imgl_uri  CC=5  out:3
    uri_for_imgl_action  CC=1  out:1
    uri_for_imgl_analyze  CC=2  out:1
    uri_for_imgl_annotate  CC=2  out:1
    uri_for_imgl_click  CC=5  out:1
    uri_for_imgl_list  CC=1  out:1
    uri_for_imgl_type  CC=5  out:1
  imgl.vdisplay_bridge  [10 funcs]
    _norm  CC=1  out:2
    build_window_control_report  CC=19  out:32
    correlate_windows  CC=18  out:32
    default_display  CC=2  out:3
    diagnose_os_display  CC=4  out:5
    find_os_window  CC=6  out:5
    list_os_monitors  CC=3  out:3
    list_os_windows  CC=3  out:3
    list_vision_windows  CC=4  out:11
    vdisplay_missing_message  CC=2  out:4
  imgl.web.agent  [2 funcs]
    _parse_agent_json  CC=6  out:7
    pick_agent_action  CC=20  out:23
  imgl.web.app  [1 funcs]
    create_app  CC=4  out:107
  imgl.web.session  [6 funcs]
    _refresh_annotated_png  CC=3  out:6
    analyze  CC=1  out:6
    capture  CC=1  out:4
    refresh_catalog  CC=2  out:2
    resolve_prompt  CC=2  out:3
    select_window  CC=4  out:3
  imgl.web.thumbs  [2 funcs]
    _clamp_box  CC=3  out:6
    crop_bbox_png  CC=2  out:15
  imgl.window_scope  [23 funcs]
    _best_vertical_split  CC=12  out:10
    _collect_elements  CC=2  out:2
    _detect_layout_mode  CC=12  out:16
    _element_gap_gutters  CC=6  out:9
    _guess_window_title  CC=6  out:6
    _image_gutter_candidates  CC=14  out:19
    _regions_from_balanced_gutters  CC=18  out:17
    _safe_filename  CC=6  out:5
    _shift_elements  CC=2  out:5
    _shift_ocr_boxes  CC=2  out:3
  packages.cli2imgl.src.cli2imgl.cli  [1 funcs]
    main  CC=6  out:14
  packages.dsl2imgl.src.dsl2imgl.bus  [5 funcs]
    _run_handler  CC=2  out:7
    dispatch  CC=10  out:21
    dispatch_json  CC=1  out:2
    execute_dsl  CC=4  out:6
    execute_dsl_line  CC=1  out:1
  packages.dsl2imgl.src.dsl2imgl.codec  [7 funcs]
    envelope_from_bytes  CC=1  out:2
    envelope_from_json  CC=2  out:5
    envelope_to_bytes  CC=1  out:2
    envelope_to_json  CC=1  out:3
    parse_text  CC=2  out:2
    roundtrip_text  CC=1  out:4
    validate_payload  CC=2  out:6
  packages.dsl2imgl.src.dsl2imgl.events  [2 funcs]
    _append_jsonl  CC=3  out:27
    _append_pb  CC=3  out:27
  packages.dsl2imgl.src.dsl2imgl.grammar  [4 funcs]
    parse_line  CC=44  out:46
    pick_flag  CC=3  out:2
    split_command  CC=4  out:4
    to_text  CC=10  out:20
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime  [7 funcs]
    _build_interact_session  CC=4  out:12
    _run_prompt_act  CC=8  out:15
    handle_actions  CC=4  out:11
    handle_analyze  CC=4  out:10
    handle_capture  CC=3  out:9
    handle_execute  CC=14  out:35
    handle_resolve  CC=7  out:14
  packages.dsl2imgl.src.dsl2imgl.pb_codec  [9 funcs]
    _set_body  CC=31  out:73
    decode_protobuf  CC=1  out:3
    decode_protobuf_to_text  CC=1  out:2
    dict_to_envelope  CC=1  out:5
    encode_protobuf  CC=1  out:2
    encode_result_protobuf  CC=1  out:2
    encode_text_to_protobuf  CC=2  out:3
    envelope_to_dict  CC=42  out:6
    result_to_pb  CC=3  out:3
  packages.dsl2imgl.src.dsl2imgl.schema_registry  [4 funcs]
    _load_schemas  CC=4  out:11
    all_verbs  CC=1  out:3
    schema_for_verb  CC=2  out:4
    validate_schemas  CC=3  out:6
  packages.mcp2imgl.src.mcp2imgl.cli  [1 funcs]
    main  CC=2  out:5
  packages.mcp2imgl.src.mcp2imgl.server  [1 funcs]
    run_stdio  CC=2  out:12
  packages.nlp2imgl.src.nlp2imgl.control  [5 funcs]
    _result_to_dict  CC=4  out:13
    apply_nl_with_diag  CC=17  out:16
    default_image_path  CC=3  out:5
    default_window  CC=3  out:2
    doctor_capture  CC=2  out:4
  packages.nlp2imgl.src.nlp2imgl.to_dsl  [3 funcs]
    apply_nl  CC=5  out:7
    to_dsl  CC=15  out:19
    use_llm_enabled  CC=4  out:6
  packages.rest2imgl.src.rest2imgl.cli  [1 funcs]
    main  CC=2  out:8
  packages.uri2imgl.src.uri2imgl.cli  [1 funcs]
    main  CC=4  out:15
  packages.uri2imgl.src.uri2imgl.decode  [1 funcs]
    uri_to_dsl  CC=18  out:16
  scripts.imgl-capture  [1 funcs]
    mark_capture_fresh  CC=0  out:0
  scripts.imgl-verify-capture  [1 funcs]
    print  CC=0  out:0

EDGES:
  packages.rest2imgl.src.rest2imgl.cli.main → imgl.web.app.create_app
  packages.cli2imgl.src.cli2imgl.cli.main → scripts.imgl-verify-capture.print
  packages.cli2imgl.src.cli2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.cli2imgl.src.cli2imgl.cli.main → packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.mcp2imgl.src.mcp2imgl.cli.main → packages.mcp2imgl.src.mcp2imgl.server.run_stdio
  packages.mcp2imgl.src.mcp2imgl.server.run_stdio → packages.nlp2imgl.src.nlp2imgl.to_dsl.to_dsl
  packages.mcp2imgl.src.mcp2imgl.server.run_stdio → packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.bus._run_handler
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.grammar.to_text
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.bus.execute_dsl_line → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.dsl2imgl.src.dsl2imgl.bus.execute_dsl → packages.dsl2imgl.src.dsl2imgl.bus.execute_dsl_line
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch_json → packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_json
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch_json → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb → packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl → packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb
  packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope → packages.dsl2imgl.src.dsl2imgl.pb_codec._set_body
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
  packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.envelope_to_dict
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_text_to_protobuf → packages.dsl2imgl.src.dsl2imgl.grammar.parse_line
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_text_to_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf
  packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf_to_text → packages.dsl2imgl.src.dsl2imgl.grammar.to_text
  packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf_to_text → packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_result_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb
  packages.dsl2imgl.src.dsl2imgl.schema_registry.schema_for_verb → packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas
  packages.dsl2imgl.src.dsl2imgl.schema_registry.all_verbs → packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas
  packages.dsl2imgl.src.dsl2imgl.schema_registry.validate_schemas → packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas
  packages.dsl2imgl.src.dsl2imgl.codec.validate_payload → packages.dsl2imgl.src.dsl2imgl.schema_registry.schema_for_verb
  packages.dsl2imgl.src.dsl2imgl.codec.parse_text → packages.dsl2imgl.src.dsl2imgl.grammar.parse_line
  packages.dsl2imgl.src.dsl2imgl.codec.parse_text → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_bytes → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_bytes → packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes → packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_json → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_json → packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.codec.parse_text
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.codec.envelope_from_bytes
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.grammar.to_text
  packages.dsl2imgl.src.dsl2imgl.codec.roundtrip_text → packages.dsl2imgl.src.dsl2imgl.codec.envelope_to_bytes
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.scene_cache.load_or_analyze
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.window_scope.apply_discovered_windows
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.interact._build_session_catalog
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session → imgl.window_scope.summarize_windows
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime._run_prompt_act → imgl.nlp2uri.prompt_to_imgl_uri
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 117f 59623L | python:76,shell:13,json:12,toml:7,yaml:6,proto:2 | 2026-06-09
# generated in 0.03s
# CC̅=5.3 | critical:27/379 | dups:0 | cycles:3

HEALTH[20]:
  🔴 CYCLE Circular dependency detected: imgl.llm_catalog._snap_options_to_scene -> imgl.catalog.build_interactive_catalog -> imgl.llm_catalog.refine_catalog_with_llm. This indicates high coupling and may lead to infinite recursion or initialization issues.
  🔴 CYCLE Circular dependency detected: imgl.catalog.build_interactive_catalog -> imgl.llm_catalog.refine_catalog_with_llm -> imgl.llm_catalog._merge_heuristic_inputs -> imgl.llm_catalog._heuristic_fallback. This indicates high coupling and may lead to infinite recursion or initialization issues.
  🔴 CYCLE Circular dependency detected: imgl.catalog.build_interactive_catalog -> imgl.llm_catalog.refine_catalog_with_llm -> imgl.llm_catalog._heuristic_fallback. This indicates high coupling and may lead to infinite recursion or initialization issues.
  🟡 CC    uri_to_dsl CC=18 (limit:15)
  🟡 CC    _set_body CC=31 (limit:15)
  🟡 CC    envelope_to_dict CC=42 (limit:15)
  🟡 CC    prompt_to_imgl_uri CC=28 (limit:15)
  🟡 CC    _resolve_click CC=17 (limit:15)
  🟡 CC    _resolve_type CC=30 (limit:15)
  🟡 CC    run_interactive_shell CC=43 (limit:15)
  🟡 CC    _keep_element CC=17 (limit:15)
  🟡 CC    scene_to_vql CC=16 (limit:15)
  🟡 CC    _detect_buttons CC=24 (limit:15)
  🟡 CC    _detect_panels_simple CC=23 (limit:15)
  🟡 CC    act CC=29 (limit:15)
  🟡 CC    pick_agent_action CC=20 (limit:15)
  🟡 CC    classify_scene_elements CC=27 (limit:15)
  🟡 CC    parse_line CC=44 (limit:15)
  🟡 CC    main CC=15 (limit:15)
  🟡 CC    to_dsl CC=15 (limit:15)

REFACTOR[2]:
  1. split 17 high-CC methods  (CC>15)
  2. break 3 circular dependencies

PIPELINES[78]:
  [1] Src [main]: main → create_app → pick_agent_action → _load_env_files → ...(1 more)
      PURITY: 100% pure
  [2] Src [main]: main → print
      PURITY: 100% pure
  [3] Src [main]: main → uri_to_dsl
      PURITY: 100% pure
  [4] Src [main]: main → run_stdio → to_dsl → use_llm_enabled
      PURITY: 100% pure
  [5] Src [execute_dsl]: execute_dsl → execute_dsl_line → dispatch → _run_handler
      PURITY: 100% pure
  [6] Src [dispatch_json]: dispatch_json → envelope_from_json → validate_payload → schema_for_verb → ...(1 more)
      PURITY: 100% pure
  [7] Src [main]: main → dispatch → _run_handler
      PURITY: 100% pure
  [8] Src [to_dict]: to_dict
      PURITY: 100% pure
  [9] Src [for_default]: for_default
      PURITY: 100% pure
  [10] Src [append_command]: append_command
      PURITY: 100% pure
  [11] Src [_append_pb]: _append_pb → dict_to_envelope → _set_body
      PURITY: 100% pure
  [12] Src [_append_jsonl]: _append_jsonl → dict_to_envelope → _set_body
      PURITY: 100% pure
  [13] Src [replay_pb]: replay_pb → envelope_to_dict
      PURITY: 100% pure
  [14] Src [replay]: replay
      PURITY: 100% pure
  [15] Src [encode_text_to_protobuf]: encode_text_to_protobuf → parse_line → split_command
      PURITY: 100% pure
  [16] Src [decode_protobuf_to_text]: decode_protobuf_to_text → to_text
      PURITY: 100% pure
  [17] Src [all_verbs]: all_verbs → _load_schemas
      PURITY: 100% pure
  [18] Src [validate_schemas]: validate_schemas → _load_schemas
      PURITY: 100% pure
  [19] Src [envelope_to_json]: envelope_to_json → validate_payload → schema_for_verb → _load_schemas
      PURITY: 100% pure
  [20] Src [roundtrip_text]: roundtrip_text → parse_text → parse_line → split_command
      PURITY: 100% pure
  [21] Src [to_json]: to_json
      PURITY: 100% pure
  [22] Src [handle_health]: handle_health
      PURITY: 100% pure
  [23] Src [handle_capture]: handle_capture → capture_screen → default_capture_path
      PURITY: 100% pure
  [24] Src [handle_analyze]: handle_analyze → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure
  [25] Src [handle_actions]: handle_actions → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure
  [26] Src [handle_resolve]: handle_resolve → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure
  [27] Src [handle_execute]: handle_execute → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure
  [28] Src [main]: main → print
      PURITY: 100% pure
  [29] Src [_match_catalog_action]: _match_catalog_action → _find_catalog_input
      PURITY: 100% pure
  [30] Src [assign_ocr_to_windows]: assign_ocr_to_windows → find_containing_window → center_in
      PURITY: 100% pure
  [31] Src [uri_for_imgl_action]: uri_for_imgl_action → _imgl_uri
      PURITY: 100% pure
  [32] Src [resolve_image_path_optional]: resolve_image_path_optional → resolve_image_path
      PURITY: 100% pure
  [33] Src [contains]: contains
      PURITY: 100% pure
  [34] Src [from_xyxy]: from_xyxy
      PURITY: 100% pure
  [35] Src [to_dict]: to_dict
      PURITY: 100% pure
  [36] Src [to_dict]: to_dict
      PURITY: 100% pure
  [37] Src [to_dict]: to_dict
      PURITY: 100% pure
  [38] Src [to_dict]: to_dict
      PURITY: 100% pure
  [39] Src [from_dict]: from_dict
      PURITY: 100% pure
  [40] Src [dataclass_to_dict]: dataclass_to_dict
      PURITY: 100% pure
  [41] Src [write_annotated_images_per_window]: write_annotated_images_per_window → write_annotated_image → scene_to_annotated_image → _load_fonts → ...(1 more)
      PURITY: 100% pure
  [42] Src [detect_ui_elements]: detect_ui_elements → _detect_titlebar → _avg_color
      PURITY: 100% pure
  [43] Src [run]: run → ocr_lang_attempts → normalize_ocr_lang
      PURITY: 100% pure
  [44] Src [create_app]: create_app
      PURITY: 100% pure
  [45] Src [to_dict]: to_dict
      PURITY: 100% pure
  [46] Src [__post_init__]: __post_init__
      PURITY: 100% pure
  [47] Src [refresh_catalog]: refresh_catalog → build_interactive_catalog → actions
      PURITY: 100% pure
  [48] Src [analyze]: analyze → load_or_analyze → analyze → preprocess → ...(2 more)
      PURITY: 100% pure
  [49] Src [capture]: capture → capture_screen → default_capture_path
      PURITY: 100% pure
  [50] Src [select_window]: select_window → get_discovered_window → discover_windows → is_monolithic_scene
      PURITY: 100% pure

LAYERS:
  examples/                       CC̄=7.0    ←in:0  →out:0
  │ demo-nlp2uri                79L  0C    1m  CC=7      ←0
  │ demo-agent-loop.sh          37L  0C    0m  CC=0.0    ←0
  │ demo-windows.sh             22L  0C    0m  CC=0.0    ←0
  │ demo-github.sh              21L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=5.7    ←in:0  →out:0
  │ !! pb_codec                   240L  0C   10m  CC=42     ←3
  │ runtime                    220L  0C    8m  CC=14     ←0
  │ events                     168L  2C    8m  CC=6      ←0
  │ !! control                    150L  0C    5m  CC=17     ←2
  │ !! grammar                    137L  0C    4m  CC=44     ←3
  │ app                        125L  2C    1m  CC=1      ←0
  │ bus                        110L  0C    5m  CC=10     ←6
  │ !! to_dsl                      93L  0C    3m  CC=15     ←5
  │ !! cli                         91L  0C    1m  CC=15     ←0
  │ command.proto               83L  0C    0m  CC=0.0    ←0
  │ codec                       57L  0C    7m  CC=2      ←1
  │ command_pb2                 56L  0C    0m  CC=0.0    ←0
  │ cli                         46L  0C    1m  CC=9      ←0
  │ schema_registry             44L  0C    4m  CC=4      ←1
  │ result_pb2                  39L  0C    0m  CC=0.0    ←0
  │ cli                         36L  0C    1m  CC=4      ←0
  │ !! decode                      35L  0C    1m  CC=18     ←1
  │ server                      35L  0C    1m  CC=2      ←1
  │ cli                         34L  0C    1m  CC=6      ←0
  │ result                      34L  1C    2m  CC=1      ←0
  │ pyproject.toml              27L  0C    0m  CC=0.0    ←0
  │ cli                         26L  0C    1m  CC=2      ←0
  │ result.proto                23L  0C    0m  CC=0.0    ←0
  │ cli                         22L  0C    1m  CC=2      ←0
  │ pyproject.toml              21L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ type.schema.json            14L  0C    0m  CC=0.0    ←0
  │ click.schema.json           14L  0C    0m  CC=0.0    ←0
  │ execute.schema.json         13L  0C    0m  CC=0.0    ←0
  │ agent.schema.json           13L  0C    0m  CC=0.0    ←0
  │ analyze.schema.json         13L  0C    0m  CC=0.0    ←0
  │ key.schema.json             13L  0C    0m  CC=0.0    ←0
  │ resolve.schema.json         12L  0C    0m  CC=0.0    ←0
  │ actions.schema.json         12L  0C    0m  CC=0.0    ←0
  │ capture.schema.json         11L  0C    0m  CC=0.0    ←0
  │ health.schema.json           9L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ generate-proto.sh            6L  0C    0m  CC=0.0    ←0
  │ engine                       5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  imgl/                           CC̄=5.4    ←in:63  →out:102  !! split
  │ !! cli                        717L  0C    7m  CC=44     ←0
  │ !! window_scope               575L  1C   25m  CC=18     ←10
  │ !! interact                   560L  1C   11m  CC=43     ←4
  │ !! llm_catalog                520L  0C   16m  CC=14     ←2
  │ !! session                    452L  5C   18m  CC=29     ←0
  │ !! autodiag                   406L  0C   21m  CC=24     ←3
  │ catalog                    350L  1C    9m  CC=13     ←6
  │ annotate_export            299L  0C   14m  CC=8      ←3
  │ app                        286L  6C    1m  CC=4      ←2
  │ !! nlp2uri                    282L  1C    6m  CC=28     ←4
  │ !! local                      278L  1C    9m  CC=24     ←0
  │ !! actions                    271L  4C   16m  CC=21     ←3
  │ !! gui_heuristics             261L  0C    9m  CC=27     ←1
  │ !! vdisplay_bridge            253L  0C   12m  CC=19     ←1
  │ diagnose                   247L  1C   10m  CC=10     ←4
  │ !! vql_adapter                244L  0C   10m  CC=16     ←3
  │ capture                    211L  2C   13m  CC=13     ←3
  │ types                      170L  5C   10m  CC=5      ←0
  │ execute                    162L  1C    6m  CC=9      ←3
  │ !! agent                      152L  0C    4m  CC=20     ←1
  │ freshness                  151L  0C    9m  CC=5      ←2
  │ html_export                149L  0C    7m  CC=8      ←1
  │ !! catalog_filter             138L  0C    6m  CC=17     ←2
  │ svg_export                 137L  0C    7m  CC=4      ←1
  │ uri                        118L  0C    7m  CC=5      ←4
  │ pipeline                   116L  0C    3m  CC=11     ←3
  │ layout                     108L  0C    6m  CC=10     ←2
  │ rectangles                  96L  0C    5m  CC=14     ←1
  │ tesseract                   94L  1C    2m  CC=13     ←0
  │ coords                      70L  0C    1m  CC=6      ←1
  │ img2vql_bridge              64L  0C    4m  CC=4      ←1
  │ scene_cache                 63L  0C    4m  CC=5      ←5
  │ preprocess                  63L  1C    2m  CC=3      ←1
  │ thumbs                      55L  0C    3m  CC=3      ←1
  │ __init__                    51L  0C    0m  CC=0.0    ←0
  │ paths                       41L  0C    2m  CC=5      ←6
  │ geometry                    37L  0C    4m  CC=3      ←8
  │ lang                        32L  0C    2m  CC=6      ←1
  │ __init__                    30L  0C    0m  CC=0.0    ←0
  │ config                      23L  1C    0m  CC=0.0    ←0
  │ json_export                 22L  0C    2m  CC=2      ←2
  │ _escape                     19L  0C    2m  CC=1      ←2
  │ base                        14L  1C    1m  CC=1      ←0
  │ __init__                    12L  0C    1m  CC=2      ←1
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    1m  CC=1      ←0
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │
  scripts/                        CC̄=0.0    ←in:97  →out:0
  │ imgl-capture.sh            115L  0C    4m  CC=0.0    ←2
  │ install-img2nl.sh           22L  0C    0m  CC=0.0    ←0
  │ install-vdisplay.sh         22L  0C    0m  CC=0.0    ←0
  │ imgl-execute.sh             22L  0C    0m  CC=0.0    ←0
  │ imgl-windows.sh             21L  0C    0m  CC=0.0    ←0
  │ imgl-verify-capture.sh      20L  0C    1m  CC=0.0    ←7
  │ imgl-doctor.sh              20L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! layout.vql.json          46316L  0C    0m  CC=0.0    ←0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  511L  0C    0m  CC=0.0    ←0
  │ Makefile                   150L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             101L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │ screen.vql.imgl.json         0L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    39L  0C    0m  CC=0.0    ←0
  │ generated-api-integration.testql.toon.yaml    18L  0C    0m  CC=0.0    ←0
  │ generated-from-pytests.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     screen.vql.imgl.json                      0L

COUPLING:
                                    imgl             scripts         imgl.export   packages.nlp2imgl   packages.dsl2imgl            imgl.web    examples.scripts       imgl.classify  packages.rest2imgl         imgl.detect   packages.cli2imgl   packages.mcp2imgl   packages.uri2imgl
                imgl                  ──                  77                  21                 ←13                  ←9                   1                  ←5                   1                                       2                                                              hub
             scripts                 ←77                  ──                                      ←5                  ←3                                      ←6                                                                              ←4                                      ←2  hub
         imgl.export                   7                                      ──                                                          ←2                                                                                                                                              hub
   packages.nlp2imgl                  13                   5                                      ──                   3                                                                              ←5                                      ←2                  ←2                      hub
   packages.dsl2imgl                   9                   3                                      ←3                  ──                                                                              ←4                                      ←1                  ←1                  ←1  hub
            imgl.web                  14                                       2                                                          ──                                                          ←1                                                                                  !! fan-out
    examples.scripts                   5                   6                                                                                                  ──                                                                                                                          !! fan-out
       imgl.classify                   9                                                                                                                                          ──                                                                                                      !! fan-out
  packages.rest2imgl                                                                               5                   4                   1                                                          ──                                                                                  !! fan-out
         imgl.detect                   6                                                                                                                                                                                  ──                                                            
   packages.cli2imgl                                       4                                       2                   1                                                                                                                      ──                                        
   packages.mcp2imgl                                                                               2                   1                                                                                                                                          ──                    
   packages.uri2imgl                                       2                                                           1                                                                                                                                                              ──
  CYCLES: 3
  HUB: imgl/ (fan-in=63)
  HUB: packages.dsl2imgl/ (fan-in=10)
  HUB: packages.nlp2imgl/ (fan-in=9)
  HUB: imgl.export/ (fan-in=23)
  HUB: scripts/ (fan-in=97)
  SMELL: imgl.web/ fan-out=16 → split needed
  SMELL: examples.scripts/ fan-out=11 → split needed
  SMELL: imgl/ fan-out=102 → split needed
  SMELL: packages.rest2imgl/ fan-out=10 → split needed
  SMELL: packages.dsl2imgl/ fan-out=12 → split needed
  SMELL: packages.nlp2imgl/ fan-out=21 → split needed
  SMELL: imgl.classify/ fan-out=9 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 5 groups | 76f 10328L | 2026-06-09

SUMMARY:
  files_scanned: 76
  total_lines:   10328
  dup_groups:    5
  dup_fragments: 10
  saved_lines:   44
  scan_ms:       2384

HOTSPOTS[7] (files with most duplication):
  imgl/export/html_export.py  dup=28L  groups=2  frags=2  (0.3%)
  imgl/export/svg_export.py  dup=17L  groups=2  frags=2  (0.2%)
  imgl/capture.py  dup=8L  groups=1  frags=2  (0.1%)
  imgl/detect/img2vql_bridge.py  dup=7L  groups=1  frags=1  (0.1%)
  imgl/diagnose.py  dup=7L  groups=1  frags=1  (0.1%)
  imgl/catalog.py  dup=5L  groups=1  frags=1  (0.0%)
  imgl/export/annotate_export.py  dup=5L  groups=1  frags=1  (0.0%)

DUPLICATES[5] (ranked by impact):
  [49d1d03e6ce392a1]   STRU  _base_css  L=21 N=2 saved=21 sim=1.00
      imgl/export/html_export.py:75-95  (_base_css)
      imgl/export/svg_export.py:76-85  (_svg_css)
  [00c76eba96672ce9]   EXAC  _default_title  L=7 N=2 saved=7 sim=1.00
      imgl/export/html_export.py:56-62  (_default_title)
      imgl/export/svg_export.py:56-62  (_default_title)
  [5843dfdd9fc8bd2f]   STRU  img2vql_available  L=7 N=2 saved=7 sim=1.00
      imgl/detect/img2vql_bridge.py:18-24  (img2vql_available)
      imgl/diagnose.py:16-22  (img2nl_available)
  [e4a985e7f83fe868]   STRU  _truncate  L=5 N=2 saved=5 sim=1.00
      imgl/catalog.py:346-350  (_truncate)
      imgl/export/annotate_export.py:231-235  (_short_hint_text)
  [e41d60f79f9afd0d]   STRU  _capture_with_grim  L=4 N=2 saved=4 sim=1.00
      imgl/capture.py:142-145  (_capture_with_grim)
      imgl/capture.py:154-157  (_capture_with_scrot)

REFACTOR[5] (ranked by priority):
  [1] ○ extract_function   → imgl/export/utils/_base_css.py
      WHY: 2 occurrences of 21-line block across 2 files — saves 21 lines
      FILES: imgl/export/html_export.py, imgl/export/svg_export.py
  [2] ○ extract_function   → imgl/export/utils/_default_title.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: imgl/export/html_export.py, imgl/export/svg_export.py
  [3] ○ extract_function   → imgl/utils/img2vql_available.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: imgl/detect/img2vql_bridge.py, imgl/diagnose.py
  [4] ○ extract_function   → imgl/utils/_truncate.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: imgl/catalog.py, imgl/export/annotate_export.py
  [5] ○ extract_function   → imgl/utils/_capture_with_grim.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: imgl/capture.py

QUICK_WINS[3] (low risk, high savings — do first):
  [1] extract_function   saved=21L  → imgl/export/utils/_base_css.py
      FILES: html_export.py, svg_export.py
  [2] extract_function   saved=7L  → imgl/export/utils/_default_title.py
      FILES: html_export.py, svg_export.py
  [3] extract_function   saved=7L  → imgl/utils/img2vql_available.py
      FILES: img2vql_bridge.py, diagnose.py

EFFORT_ESTIMATE (total ≈ 1.5h):
  medium _base_css                           saved=21L  ~42min
  easy   _default_title                      saved=7L  ~14min
  easy   img2vql_available                   saved=7L  ~14min
  easy   _truncate                           saved=5L  ~10min
  easy   _capture_with_grim                  saved=4L  ~8min

METRICS-TARGET:
  dup_groups:  5 → 0
  saved_lines: 44 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 373 func | 61f | 2026-06-09
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !! SPLIT-FUNC      main  CC=44  fan=45
      WHY: CC=44 exceeds 15
      EFFORT: ~1h  IMPACT: 1980

  [2] !! SPLIT-FUNC      run_interactive_shell  CC=43  fan=35
      WHY: CC=43 exceeds 15
      EFFORT: ~1h  IMPACT: 1505

  [3] !! SPLIT-FUNC      prompt_to_imgl_uri  CC=28  fan=24
      WHY: CC=28 exceeds 15
      EFFORT: ~1h  IMPACT: 672

  [4] !  SPLIT-FUNC      _detect_buttons  CC=24  fan=26
      WHY: CC=24 exceeds 15
      EFFORT: ~1h  IMPACT: 624

  [5] !  SPLIT-FUNC      _run_image_command  CC=19  fan=28
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 532

  [6] !! SPLIT-FUNC      parse_line  CC=44  fan=12
      WHY: CC=44 exceeds 15
      EFFORT: ~1h  IMPACT: 528

  [7] !! SPLIT-FUNC      classify_scene_elements  CC=27  fan=17
      WHY: CC=27 exceeds 15
      EFFORT: ~1h  IMPACT: 459

  [8] !  SPLIT-FUNC      build_window_control_report  CC=19  fan=24
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 456

  [9] !! SPLIT-FUNC      WebSession.act  CC=29  fan=15
      WHY: CC=29 exceeds 15
      EFFORT: ~1h  IMPACT: 435

  [10] !  SPLIT-FUNC      _detect_panels_simple  CC=23  fan=16
      WHY: CC=23 exceeds 15
      EFFORT: ~1h  IMPACT: 368


RISKS[3]:
  ⚠ Splitting layout.vql.json may break 0 import paths
  ⚠ Splitting screen.vql.imgl.json may break 0 import paths
  ⚠ Splitting planfile.yaml may break 0 import paths

METRICS-TARGET:
  CC̄:          5.4 → ≤3.8
  max-CC:      44 → ≤20
  god-modules: 8 → 0
  high-CC(≥15): 27 → ≤13
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=5.3 → now CC̄=5.4
```

## Intent

Image to Layout — screenshot OCR and semantic UI reconstruction
