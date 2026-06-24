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
- **version**: `0.7.12`
- **python_requires**: `>=3.10,<3.14`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(3), app.doql.less, goal.yaml, .env.example, src(33 mod), project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: imgl;
  version: 0.7.12;
}

dependencies {
  runtime: "pillow>=10.0, pytesseract>=0.3.10, PyYAML>=6.0";
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

interface[type="web"] {
  type: spa;
  framework: static;
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
  step-2: run cmd=$(IMGL) install control;
  step-3: run cmd=if [ -d "$(VDISPLAY_ROOT)" ]; then \;
  step-4: run cmd=$(PIP) install -e "$(VDISPLAY_ROOT)[pillow]" || $(PIP) install -e "$(VDISPLAY_ROOT)"; \;
  step-5: run cmd=fi;
}

workflow[name="install-control"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) install control;
}

workflow[name="install-img2nl"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) install img2nl;
}

workflow[name="install-vdisplay"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) install vdisplay;
}

workflow[name="install-vql"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) install vql;
}

workflow[name="install-full"] {
  trigger: manual;
  step-1: run cmd=$(PIP) install -e ".[web]";
}

workflow[name="capture"] {
  trigger: manual;
  step-1: run cmd=$(IMGL) capture --smart -o "$(IMGL_IMAGE)";
}

workflow[name="capture-interactive"] {
  trigger: manual;
  step-1: run cmd=rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.capture.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)";
  step-2: run cmd=IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture --portal -o "$(IMGL_IMAGE)" --verify;
  step-3: run cmd=rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)";
  step-4: run cmd=echo "export IMGL_IMAGE=$(IMGL_IMAGE)";
}

workflow[name="capture-analyze"] {
  trigger: manual;
  step-1: run cmd=rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.capture.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)";
  step-2: run cmd=IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture --portal -o "$(IMGL_IMAGE)" --verify --analyze;
  step-3: run cmd=echo "export IMGL_IMAGE=$(IMGL_IMAGE)";
}

workflow[name="verify-capture"] {
  trigger: manual;
  step-1: run cmd=BEFORE=$${BEFORE:-$$(stat -c %Y "$(IMGL_IMAGE)" 2>/dev/null || echo 0)}; \;
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
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-analyze (lub make capture-interactive)" && exit 1);
  step-2: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make execute PROMPT='wpisz test w Chat input'" && exit 1);
  step-3: run cmd=$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)";
}

workflow[name="execute-dry"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-analyze (lub make capture-interactive)" && exit 1);
  step-2: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make execute-dry PROMPT='wpisz test w Chat input'" && exit 1);
  step-3: run cmd=$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --dry-run --format "$(FORMAT)";
}

workflow[name="execute-llm"] {
  trigger: manual;
  step-1: run cmd=test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-analyze (lub make capture-interactive)" && exit 1);
  step-2: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make execute-llm PROMPT='wpisz test w Chat input'" && exit 1);
  step-3: run cmd=test -n "$$OPENROUTER_API_KEY" || (echo "Brak OPENROUTER_API_KEY" && exit 1);
  step-4: run cmd=$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --llm --format "$(FORMAT)";
}

workflow[name="shot"] {
  trigger: manual;
  step-1: run cmd=test -n "$(PROMPT)" || (echo "Użycie: make shot PROMPT='wpisz test w Chat input'" && exit 1);
  step-2: run cmd=$(IMGL) shot "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)";
}

workflow[name="test"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m pytest tests packages/dsl2imgl/tests -q;
}

workflow[name="test-imgl"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m pytest tests/test_autodiag.py tests/test_vdisplay_bridge.py tests/test_nlp2imgl_control.py tests/test_control_cli.py tests/test_installs.py -q;
}

workflow[name="test-dsl2imgl"] {
  trigger: manual;
  step-1: run cmd=$(PY) -m pytest packages/dsl2imgl/tests -q;
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
  step-1: run cmd=$(IMGL) serve --port $(WEB_PORT) --image screen.png --llm --window region-bottom;
}

workflow[name="demo-key"] {
  trigger: manual;
  step-1: run cmd=$(VENV)/bin/dsl2imgl exec 'KEY ctrl+Return EXECUTE 0';
}

workflow[name="demo-nl"] {
  trigger: manual;
  step-1: run cmd=test -f screen.png || (echo "Brak screen.png — uruchom: imgl capture --interactive -o screen.png" && exit 1);
  step-2: run cmd=$(VENV)/bin/nlp2imgl apply "wpisz test w Chat input" --image screen.png --window region-bottom --dry-run;
}

workflow[name="demo-chat"] {
  trigger: manual;
  step-1: run cmd=test -f screen.png || (echo "Brak screen.png" && exit 1);
  step-2: run cmd=$(VENV)/bin/nlp2imgl apply "wpisz demo w Chat input" --image screen.png --window region-bottom --dry-run;
  step-3: run cmd=$(VENV)/bin/nlp2imgl apply "naciśnij ctrl+enter" --image screen.png --window region-bottom --dry-run;
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
  python_version: >=3.10,<3.14;
  vars: LLM_MODEL, OPENROUTER_API_KEY;
  runtime_llm: OPENROUTER_API_KEY;
}
```

### Source Modules

- `imgl.actions`
- `imgl.autodiag`
- `imgl.capture`
- `imgl.capture_provenance`
- `imgl.catalog`
- `imgl.catalog_filter`
- `imgl.catalog_heuristic`
- `imgl.catalog_types`
- `imgl.cli`
- `imgl.config`
- `imgl.control`
- `imgl.coords`
- `imgl.diagnose`
- `imgl.execute`
- `imgl.freshness`
- `imgl.geometry`
- `imgl.installs`
- `imgl.interact`
- `imgl.layout`
- `imgl.llm_catalog`
- `imgl.nlp2uri`
- `imgl.paths`
- `imgl.pipeline`
- `imgl.preprocess`
- `imgl.scene_cache`
- `imgl.targets`
- `imgl.terminal_md`
- `imgl.types`
- `imgl.uri`
- `imgl.vdisplay_bridge`
- `imgl.vdisplay_context`
- `imgl.vision_ops`
- `imgl.window_scope`

## Workflows

## Dependencies

### Runtime

```text markpact:deps python
pillow>=10.0
pytesseract>=0.3.10
PyYAML>=6.0
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

### `imgl.autodiag` (`imgl/autodiag.py`)

```python
def img2nl_root()  # CC=1, fan=4
def img2nl_available()  # CC=1, fan=2
def _classify_verdict(diag, is_fresh, scene_class, is_blank, worth)  # CC=8, fan=1
def diagnose_capture(image_path)  # CC=9, fan=17
def _extract_result_context(result)  # CC=8, fan=3
def build_operation_step(result)  # CC=12, fan=9 ⚠
def _compact_result(result)  # CC=6, fan=3
def build_execute_report()  # CC=8, fan=7
def resolve_cli_output_format()  # CC=7, fan=1
def pick_output_format(payload, requested)  # CC=2, fan=0
def render_report(payload, fmt)  # CC=3, fan=4
def _flag_enabled()  # CC=3, fan=3
def should_block_blank_capture(capture)  # CC=2, fan=2
def should_block_stale_capture(capture)  # CC=3, fan=2
def diagnostics_enabled()  # CC=1, fan=1
def _yaml_codeblock(data)  # CC=1, fan=2
def _shell_quote(value)  # CC=3, fan=2
def _capture_next_cmd(image)  # CC=1, fan=1
def _derive_stale(capture, image)  # CC=2, fan=2
def _derive_op_failed(operation)  # CC=9, fan=4
def _capture_verdict_current_next(capture_verdict, image, capture)  # CC=6, fan=2
def _derive_current_next(report)  # CC=19, fan=8 ⚠
def _capture_payload_section(capture)  # CC=6, fan=1
def _markdown_payload(report)  # CC=14, fan=2 ⚠
def _render_markdown(report)  # CC=6, fan=7
def _overall_verdict(capture, operation)  # CC=10, fan=1 ⚠
def _capture_verdict_hints(capture, image)  # CC=6, fan=3
def _actionable_hints(report)  # CC=14, fan=5 ⚠
def _compact_features(features)  # CC=6, fan=1
def _scene_class(diag)  # CC=2, fan=2
def _parse_coords(message)  # CC=2, fan=3
def _coords_from_action(action)  # CC=3, fan=1
def _parse_typed_text(message)  # CC=2, fan=2
def _parse_keys(message)  # CC=2, fan=3
```

### `imgl.window_scope` (`imgl/window_scope.py`)

```python
def is_monolithic_scene(scene)  # CC=2, fan=2
def apply_discovered_windows(scene)  # CC=1, fan=3
def discover_windows(scene)  # CC=2, fan=3
def summarize_windows(scene)  # CC=6, fan=7
def pick_focus_window(summaries)  # CC=11, fan=5 ⚠
def should_scope_window(scene, summary)  # CC=2, fan=3
def scope_to_focus_window(image_path, scene)  # CC=5, fan=13
def scope_image_to_focus_window(image_path)  # CC=2, fan=9
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
def _score_gutter_candidate(gutter_start, gutter_end, elements, y0, y1, min_region)  # CC=10, fan=3 ⚠
def _regions_from_balanced_gutters(window_bbox, elements, candidates)  # CC=10, fan=10 ⚠
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

### `imgl.capture` (`imgl/capture.py`)

```python
def _finalize_capture(path, meta)  # CC=6, fan=4
def last_capture_meta()  # CC=1, fan=1
def _prefer_mirror()  # CC=1, fan=3
def _vql_capture_enabled()  # CC=1, fan=3
def _portal_fallback_enabled()  # CC=2, fan=4
def _vdisplay_portal_in_chain_enabled()  # CC=2, fan=4
def default_capture_path(out)  # CC=2, fan=6
def _is_wayland()  # CC=3, fan=3
def _try_mss_fallback(path)  # CC=6, fan=5
def capture_screen(out)  # CC=16, fan=16 ⚠
def _screen_recording_denied(errors)  # CC=2, fan=2
def _capture_failure_hint()  # CC=5, fan=2
def _try_vdisplay_capture(path)  # CC=10, fan=12 ⚠
def _try_vql_capture(path)  # CC=8, fan=9
def _discard_capture_file(path)  # CC=3, fan=3
def _non_portal_backends()  # CC=2, fan=2
def _portal_backends()  # CC=1, fan=1
def _try_backend_list(path, backends)  # CC=8, fan=7
def _try_portal_backends(path)  # CC=1, fan=2
def _run_command(cmd, path)  # CC=3, fan=4
def _capture_with_gnome_shell(path)  # CC=11, fan=9 ⚠
def _capture_with_grim(path)  # CC=10, fan=7 ⚠
def _capture_with_gnome_screenshot(path)  # CC=2, fan=3
def _capture_with_scrot(path)  # CC=2, fan=3
def _portal_python()  # CC=7, fan=5
def _portal_script()  # CC=5, fan=3
def _parse_portal_output(proc, path)  # CC=11, fan=6 ⚠
def _capture_with_portal(path)  # CC=6, fan=9
def _capture_with_mss(path)  # CC=1, fan=8
def _is_blank_image(path)  # CC=6, fan=13
def capture_status_message(path)  # CC=2, fan=1
class CaptureError:  # Raised when screen capture fails.
class BlankCaptureError:  # Raised when capture succeeded but image is empty/black.
```

### `imgl.cli` (`imgl/cli.py`)

```python
def _add_output_format_flags(parser)  # CC=1, fan=2
def _output_format(args)  # CC=1, fan=1
def _add_common_args(parser)  # CC=1, fan=1
def build_parser()  # CC=1, fan=7
def _write_output(content, output)  # CC=2, fan=2
def _handle_doctor(args, config)  # CC=2, fan=4
def _handle_map(args, config)  # CC=2, fan=4
def _handle_execute(args, config)  # CC=4, fan=6
def _handle_shot(args, config)  # CC=3, fan=6
def _handle_verify(args, config)  # CC=3, fan=3
def _handle_install(args, config)  # CC=6, fan=6
def _handle_serve(args, config)  # CC=10, fan=10 ⚠
def _handle_diagnose(args, config)  # CC=4, fan=8
def _handle_interact(args, config)  # CC=3, fan=6
def _handle_windows(args, config)  # CC=11, fan=18 ⚠
def _handle_capture(args, config)  # CC=13, fan=14 ⚠
def main(argv)  # CC=4, fan=9
def _check_blank_before_analyze(image_path)  # CC=5, fan=4
def _apply_config_overrides(config, args)  # CC=2, fan=1
def _handle_analyze(args, image_path, config)  # CC=1, fan=3
def _handle_html(args, image_path, config)  # CC=1, fan=3
def _handle_svg(args, image_path, config)  # CC=3, fan=4
def _handle_vql(args, image_path, config)  # CC=2, fan=5
def _handle_annotate(args, image_path, config)  # CC=4, fan=10
def _handle_find(args, image_path, config)  # CC=6, fan=11
def _run_image_command(args, image_path, config)  # CC=3, fan=5
```

### `imgl.interact` (`imgl/interact.py`)

```python
def _build_session_catalog(session)  # CC=2, fan=1
def resolve_imgl_uri(uri, session)  # CC=13, fan=16 ⚠
def _attach_image_path(payload, session)  # CC=1, fan=1
def _click_by_element_id(element_id, session)  # CC=4, fan=2
def _resolve_click(qs, finder, session)  # CC=15, fan=5 ⚠
def _resolve_type_no_value(qs, session)  # CC=7, fan=1
def _resolve_type_by_element_id(element_id, value, session)  # CC=4, fan=2
def _resolve_type_by_hints(label, text, value, session)  # CC=10, fan=3 ⚠
def _resolve_type(qs, finder, session)  # CC=14, fan=7 ⚠
def _annotate_catalog(session)  # CC=6, fan=7
def _select_window(session, window_ref)  # CC=6, fan=6
def _export_window_previews(session)  # CC=4, fan=5
def _prepare_interactive_session(image_path)  # CC=4, fan=12
def _show_initial_shell_views()  # CC=8, fan=7
def _print_actions_phase_hints()  # CC=9, fan=6
def _read_shell_prompt(stdin, stderr)  # CC=4, fan=4
def _handle_resolved_shell_action()  # CC=11, fan=7 ⚠
def run_interactive_shell(image_path)  # CC=5, fan=5
def _run_shell_loop()  # CC=11, fan=8 ⚠
def describe_resolution(resolved)  # CC=1, fan=0
def _print_catalog_banner(session, cfg, use_llm, no_filter, stderr)  # CC=8, fan=4
def _handle_window_phase_prompt(prompt)  # CC=9, fan=12
class InteractSession:
```

## Call Graph

*367 nodes · 500 edges · 57 modules · CC̄=4.6*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `build_parser` *(in imgl.cli)* | 1 | 1 | 116 | **117** |
| `diagnose_capture` *(in imgl.autodiag)* | 9 | 5 | 42 | **47** |
| `create_app` *(in packages.rest2imgl.src.rest2imgl.app)* | 1 | 2 | 36 | **38** |
| `dispatch` *(in packages.dsl2imgl.src.dsl2imgl.bus)* | 10 ⚠ | 14 | 21 | **35** |
| `handle_execute` *(in packages.dsl2imgl.src.dsl2imgl.handlers.runtime)* | 14 ⚠ | 0 | 35 | **35** |
| `execute_action` *(in imgl.execute)* | 13 ⚠ | 5 | 27 | **32** |
| `analyze` *(in imgl.pipeline)* | 11 ⚠ | 10 | 22 | **32** |
| `capture_screen` *(in imgl.capture)* | 20 ⚠ | 6 | 25 | **31** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/semcod/imgl
# generated in 0.25s
# nodes: 367 | edges: 500 | modules: 57
# CC̄=4.6

HUBS[20]:
  imgl.cli.build_parser
    CC=1  in:1  out:116  total:117
  imgl.autodiag.diagnose_capture
    CC=9  in:5  out:42  total:47
  packages.rest2imgl.src.rest2imgl.app.create_app
    CC=1  in:2  out:36  total:38
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch
    CC=10  in:14  out:21  total:35
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_execute
    CC=14  in:0  out:35  total:35
  imgl.execute.execute_action
    CC=13  in:5  out:27  total:32
  imgl.pipeline.analyze
    CC=11  in:10  out:22  total:32
  imgl.capture.capture_screen
    CC=20  in:6  out:25  total:31
  imgl.coords.scale_scene_to_screen
    CC=6  in:1  out:29  total:30
  imgl.control.capture_interactive
    CC=16  in:2  out:28  total:30
  imgl.vision_ops.match_template_png
    CC=11  in:0  out:29  total:29
  imgl.interact._handle_resolved_shell_action
    CC=11  in:1  out:27  total:28
  imgl.nlp2uri.prompt_to_imgl_uri
    CC=15  in:4  out:24  total:28
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl
    CC=3  in:0  out:27  total:27
  imgl.control.run_execute
    CC=13  in:2  out:25  total:27
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb
    CC=3  in:0  out:27  total:27
  imgl.vdisplay_bridge.build_window_control_report
    CC=10  in:3  out:23  total:26
  examples.scripts.demo-nlp2uri.main
    CC=7  in:0  out:25  total:25
  packages.nlp2imgl.src.nlp2imgl.cli_parser.build_parser
    CC=1  in:1  out:24  total:25
  packages.dsl2imgl.src.dsl2imgl.grammar.to_text
    CC=10  in:4  out:20  total:24

MODULES:
  examples.scripts.demo-nlp2uri  [1 funcs]
    main  CC=7  out:25
  imgl.actions  [11 funcs]
    _find_labeled_inputs  CC=8  out:9
    click  CC=2  out:4
    find  CC=14  out:10
    list_actions  CC=5  out:9
    type_into  CC=5  out:7
    _find_label_for_input  CC=6  out:5
    _format_query  CC=5  out:5
    _iter_elements  CC=9  out:2
    _text_matches  CC=3  out:2
    _window_matches  CC=4  out:3
  imgl.autodiag  [7 funcs]
    build_execute_report  CC=8  out:17
    diagnose_capture  CC=9  out:42
    diagnostics_enabled  CC=1  out:1
    render_report  CC=3  out:4
    resolve_cli_output_format  CC=7  out:1
    should_block_blank_capture  CC=2  out:2
    should_block_stale_capture  CC=3  out:3
  imgl.capture  [27 funcs]
    _capture_failure_hint  CC=5  out:2
    _capture_with_gnome_screenshot  CC=2  out:3
    _capture_with_portal  CC=6  out:11
    _capture_with_scrot  CC=2  out:3
    _discard_capture_file  CC=3  out:3
    _finalize_capture  CC=6  out:8
    _is_blank_image  CC=6  out:13
    _is_wayland  CC=3  out:4
    _non_portal_backends  CC=2  out:2
    _parse_portal_output  CC=11  out:8
  imgl.capture_provenance  [5 funcs]
    _correlate_os_windows  CC=10  out:13
    capture_meta_path  CC=1  out:2
    enrich_scene_provenance  CC=4  out:4
    load_capture_meta  CC=4  out:5
    save_capture_meta  CC=1  out:7
  imgl.catalog  [3 funcs]
    _truncate  CC=2  out:3
    build_interactive_catalog  CC=3  out:3
    format_catalog_table  CC=8  out:10
  imgl.catalog_filter  [7 funcs]
    _element_score  CC=9  out:5
    _keep_element  CC=7  out:6
    _renumber  CC=2  out:4
    _replace_index_in_uri  CC=1  out:0
    _text_quality_check  CC=10  out:8
    _window_score  CC=5  out:1
    filter_catalog  CC=8  out:7
  imgl.catalog_heuristic  [2 funcs]
    _find_window  CC=2  out:1
    build_heuristic_catalog  CC=10  out:9
  imgl.classify.gui_heuristics  [1 funcs]
    classify_scene_elements  CC=11  out:9
  imgl.cli  [25 funcs]
    _add_common_args  CC=1  out:5
    _apply_config_overrides  CC=2  out:1
    _check_blank_before_analyze  CC=5  out:7
    _handle_analyze  CC=1  out:3
    _handle_annotate  CC=4  out:14
    _handle_capture  CC=13  out:22
    _handle_diagnose  CC=4  out:17
    _handle_doctor  CC=2  out:5
    _handle_execute  CC=4  out:7
    _handle_find  CC=6  out:11
  imgl.control  [16 funcs]
    _control_packages_present  CC=2  out:4
    _require_nlp2imgl  CC=4  out:4
    _try_fallback_screen_png  CC=5  out:14
    _try_vdisplay_fallback  CC=5  out:6
    _vql_cache_paths  CC=1  out:2
    capture_interactive  CC=16  out:28
    clear_ocr_cache  CC=1  out:1
    default_image_path  CC=3  out:5
    default_window  CC=3  out:2
    run_doctor  CC=7  out:11
  imgl.coords  [1 funcs]
    scale_scene_to_screen  CC=6  out:29
  imgl.detect.img2vql_bridge  [1 funcs]
    detect_ui_merged  CC=4  out:2
  imgl.diagnose  [8 funcs]
    _diagnose_fallback  CC=8  out:14
    _diagnose_with_img2nl  CC=2  out:5
    _has_ui_signals  CC=7  out:11
    _scene_class  CC=2  out:6
    content_summary  CC=6  out:6
    diagnose_content  CC=3  out:7
    img2nl_available  CC=2  out:0
    worth_analyzing  CC=6  out:5
  imgl.execute  [4 funcs]
    _display_mismatch_warning  CC=8  out:8
    _normalize_keys  CC=9  out:12
    execute_action  CC=13  out:27
    execute_keys  CC=5  out:8
  imgl.export.annotate_export  [4 funcs]
    default_annotated_path  CC=3  out:3
    open_image  CC=4  out:5
    write_annotated_image  CC=1  out:5
    write_window_preview_images  CC=3  out:20
  imgl.export.html_export  [1 funcs]
    scene_to_html  CC=4  out:9
  imgl.export.json_export  [2 funcs]
    scene_from_json  CC=2  out:3
    scene_to_json  CC=1  out:2
  imgl.export.svg_export  [1 funcs]
    scene_to_svg  CC=4  out:9
  imgl.export.vql_adapter  [2 funcs]
    scene_to_vql_json  CC=1  out:2
    write_vql_program  CC=4  out:10
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
  imgl.geometry  [3 funcs]
    bbox_distance  CC=1  out:0
    center_in  CC=2  out:1
    iou  CC=3  out:7
  imgl.installs  [9 funcs]
    _auto_install_vdisplay_enabled  CC=1  out:3
    _pip_install_editable  CC=2  out:2
    _repo_root  CC=2  out:6
    ensure_vdisplay  CC=5  out:5
    install_control  CC=1  out:8
    install_img2nl  CC=2  out:5
    install_vdisplay  CC=2  out:5
    install_vql  CC=1  out:4
    vdisplay_available  CC=2  out:0
  imgl.interact  [21 funcs]
    _annotate_catalog  CC=6  out:8
    _attach_image_path  CC=1  out:1
    _build_session_catalog  CC=2  out:1
    _click_by_element_id  CC=4  out:2
    _export_window_previews  CC=4  out:6
    _handle_resolved_shell_action  CC=11  out:27
    _handle_window_phase_prompt  CC=9  out:21
    _prepare_interactive_session  CC=4  out:16
    _print_actions_phase_hints  CC=9  out:12
    _print_catalog_banner  CC=8  out:10
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
  imgl.nlp2uri  [7 funcs]
    _delegate_vql_nlp2uri  CC=5  out:6
    _find_catalog_by_text  CC=9  out:3
    _find_catalog_input  CC=9  out:4
    _match_catalog_action  CC=8  out:4
    _resolve_click_intent  CC=3  out:7
    _resolve_type_intent  CC=12  out:8
    prompt_to_imgl_uri  CC=15  out:24
  imgl.ocr  [1 funcs]
    get_ocr_backend  CC=2  out:2
  imgl.paths  [2 funcs]
    resolve_image_path  CC=5  out:11
    resolve_image_path_optional  CC=3  out:2
  imgl.pipeline  [3 funcs]
    _content_metadata  CC=1  out:6
    _count_roles  CC=4  out:2
    analyze  CC=11  out:22
  imgl.preprocess  [2 funcs]
    load_image  CC=2  out:8
    preprocess  CC=3  out:8
  imgl.scene_cache  [4 funcs]
    load_cached_scene  CC=5  out:10
    load_or_analyze  CC=5  out:7
    save_scene_cache  CC=1  out:3
    scene_cache_path  CC=2  out:3
  imgl.terminal_md  [11 funcs]
    _c  CC=1  out:1
    _color_yaml_value  CC=6  out:12
    _highlight_bash_line  CC=10  out:19
    _highlight_inline  CC=1  out:8
    _highlight_yaml_line  CC=3  out:8
    _render_fence_line  CC=3  out:3
    _render_normal_line  CC=6  out:17
    _verdict_color  CC=1  out:3
    colorize_markdown  CC=11  out:15
    print_report  CC=3  out:3
  imgl.uri  [7 funcs]
    _imgl_uri  CC=5  out:3
    uri_for_imgl_action  CC=1  out:1
    uri_for_imgl_analyze  CC=2  out:1
    uri_for_imgl_annotate  CC=2  out:1
    uri_for_imgl_click  CC=5  out:1
    uri_for_imgl_list  CC=1  out:1
    uri_for_imgl_type  CC=5  out:1
  imgl.vdisplay_bridge  [3 funcs]
    build_window_control_report  CC=10  out:23
    correlate_windows  CC=7  out:17
    list_os_windows  CC=3  out:3
  imgl.vdisplay_context  [3 funcs]
    _metadata_from_context  CC=8  out:12
    enrich_scene_from_vdisplay  CC=1  out:2
    from_vdisplay_context  CC=10  out:20
  imgl.vision_ops  [5 funcs]
    _crop_png_region  CC=1  out:7
    _png_to_gray_array  CC=1  out:5
    diff_png_bytes  CC=11  out:13
    match_template_png  CC=11  out:29
    template_available  CC=2  out:0
  imgl.window_scope  [29 funcs]
    _best_vertical_split  CC=12  out:10
    _collect_elements  CC=2  out:2
    _detect_layout_mode  CC=12  out:16
    _element_gap_gutters  CC=6  out:9
    _guess_window_title  CC=6  out:6
    _image_gutter_candidates  CC=14  out:19
    _regions_from_balanced_gutters  CC=10  out:14
    _safe_filename  CC=6  out:5
    _score_gutter_candidate  CC=10  out:4
    _shift_elements  CC=2  out:5
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
  packages.dsl2imgl.src.dsl2imgl.grammar  [16 funcs]
    _apply_image_window_flags  CC=3  out:2
    _parse_actions  CC=4  out:1
    _parse_agent  CC=3  out:7
    _parse_analyze  CC=5  out:2
    _parse_capture  CC=5  out:3
    _parse_click  CC=3  out:5
    _parse_execute  CC=1  out:3
    _parse_interaction_verb  CC=5  out:8
    _parse_key  CC=5  out:3
    _parse_resolve  CC=1  out:2
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime  [7 funcs]
    _build_interact_session  CC=4  out:12
    _run_prompt_act  CC=8  out:15
    handle_actions  CC=4  out:11
    handle_analyze  CC=4  out:10
    handle_capture  CC=5  out:21
    handle_execute  CC=14  out:35
    handle_resolve  CC=7  out:14
  packages.dsl2imgl.src.dsl2imgl.pb_codec  [31 funcs]
    _assign_execute_flag  CC=1  out:2
    _assign_optional_str  CC=2  out:3
    _dict_actions_body  CC=3  out:1
    _dict_agent_body  CC=2  out:3
    _dict_analyze_body  CC=3  out:2
    _dict_capture_body  CC=2  out:1
    _dict_click_body  CC=2  out:5
    _dict_execute_body  CC=1  out:3
    _dict_execute_flag  CC=2  out:0
    _dict_key_body  CC=2  out:3
  packages.dsl2imgl.src.dsl2imgl.schema_registry  [4 funcs]
    _load_schemas  CC=4  out:11
    all_verbs  CC=1  out:3
    schema_for_verb  CC=2  out:4
    validate_schemas  CC=3  out:6
  packages.mcp2imgl.src.mcp2imgl.cli  [1 funcs]
    main  CC=2  out:5
  packages.mcp2imgl.src.mcp2imgl.server  [1 funcs]
    run_stdio  CC=2  out:12
  packages.nlp2imgl.src.nlp2imgl.cli  [1 funcs]
    main  CC=1  out:3
  packages.nlp2imgl.src.nlp2imgl.cli_commands  [5 funcs]
    _print_apply_payload  CC=3  out:7
    output_format  CC=1  out:1
    run_apply  CC=6  out:8
    run_doctor  CC=6  out:13
    run_to_dsl  CC=1  out:2
  packages.nlp2imgl.src.nlp2imgl.cli_parser  [1 funcs]
    build_parser  CC=1  out:24
  packages.nlp2imgl.src.nlp2imgl.control  [6 funcs]
    _blocked_capture_response  CC=1  out:1
    _result_to_dict  CC=4  out:13
    apply_nl_with_diag  CC=17  out:16
    default_image_path  CC=3  out:5
    default_window  CC=3  out:2
    doctor_capture  CC=2  out:4
  packages.nlp2imgl.src.nlp2imgl.to_dsl  [4 funcs]
    _dispatch_dsl_command  CC=11  out:16
    apply_nl  CC=5  out:7
    to_dsl  CC=5  out:4
    use_llm_enabled  CC=5  out:7
  packages.rest2imgl.src.rest2imgl.app  [1 funcs]
    create_app  CC=1  out:36
  packages.rest2imgl.src.rest2imgl.cli  [1 funcs]
    main  CC=2  out:8
  packages.uri2imgl.src.uri2imgl.cli  [1 funcs]
    main  CC=4  out:15
  packages.uri2imgl.src.uri2imgl.decode  [3 funcs]
    _dsl_click  CC=4  out:2
    _dsl_type  CC=4  out:3
    uri_to_dsl  CC=12  out:13

EDGES:
  packages.rest2imgl.src.rest2imgl.cli.main → packages.rest2imgl.src.rest2imgl.app.create_app
  packages.cli2imgl.src.cli2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.cli2imgl.src.cli2imgl.cli.main → packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl → packages.uri2imgl.src.uri2imgl.decode._dsl_click
  packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl → packages.uri2imgl.src.uri2imgl.decode._dsl_type
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
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_capture_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_analyze_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_actions_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_resolve_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_agent_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_capture_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_analyze_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_actions_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_resolve_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_agent_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope → packages.dsl2imgl.src.dsl2imgl.pb_codec._set_body
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
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
# generated in 0.25s
# nodes: 367 | edges: 500 | modules: 57
# CC̄=4.6

HUBS[20]:
  imgl.cli.build_parser
    CC=1  in:1  out:116  total:117
  imgl.autodiag.diagnose_capture
    CC=9  in:5  out:42  total:47
  packages.rest2imgl.src.rest2imgl.app.create_app
    CC=1  in:2  out:36  total:38
  packages.dsl2imgl.src.dsl2imgl.bus.dispatch
    CC=10  in:14  out:21  total:35
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_execute
    CC=14  in:0  out:35  total:35
  imgl.execute.execute_action
    CC=13  in:5  out:27  total:32
  imgl.pipeline.analyze
    CC=11  in:10  out:22  total:32
  imgl.capture.capture_screen
    CC=20  in:6  out:25  total:31
  imgl.coords.scale_scene_to_screen
    CC=6  in:1  out:29  total:30
  imgl.control.capture_interactive
    CC=16  in:2  out:28  total:30
  imgl.vision_ops.match_template_png
    CC=11  in:0  out:29  total:29
  imgl.interact._handle_resolved_shell_action
    CC=11  in:1  out:27  total:28
  imgl.nlp2uri.prompt_to_imgl_uri
    CC=15  in:4  out:24  total:28
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl
    CC=3  in:0  out:27  total:27
  imgl.control.run_execute
    CC=13  in:2  out:25  total:27
  packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb
    CC=3  in:0  out:27  total:27
  imgl.vdisplay_bridge.build_window_control_report
    CC=10  in:3  out:23  total:26
  examples.scripts.demo-nlp2uri.main
    CC=7  in:0  out:25  total:25
  packages.nlp2imgl.src.nlp2imgl.cli_parser.build_parser
    CC=1  in:1  out:24  total:25
  packages.dsl2imgl.src.dsl2imgl.grammar.to_text
    CC=10  in:4  out:20  total:24

MODULES:
  examples.scripts.demo-nlp2uri  [1 funcs]
    main  CC=7  out:25
  imgl.actions  [11 funcs]
    _find_labeled_inputs  CC=8  out:9
    click  CC=2  out:4
    find  CC=14  out:10
    list_actions  CC=5  out:9
    type_into  CC=5  out:7
    _find_label_for_input  CC=6  out:5
    _format_query  CC=5  out:5
    _iter_elements  CC=9  out:2
    _text_matches  CC=3  out:2
    _window_matches  CC=4  out:3
  imgl.autodiag  [7 funcs]
    build_execute_report  CC=8  out:17
    diagnose_capture  CC=9  out:42
    diagnostics_enabled  CC=1  out:1
    render_report  CC=3  out:4
    resolve_cli_output_format  CC=7  out:1
    should_block_blank_capture  CC=2  out:2
    should_block_stale_capture  CC=3  out:3
  imgl.capture  [27 funcs]
    _capture_failure_hint  CC=5  out:2
    _capture_with_gnome_screenshot  CC=2  out:3
    _capture_with_portal  CC=6  out:11
    _capture_with_scrot  CC=2  out:3
    _discard_capture_file  CC=3  out:3
    _finalize_capture  CC=6  out:8
    _is_blank_image  CC=6  out:13
    _is_wayland  CC=3  out:4
    _non_portal_backends  CC=2  out:2
    _parse_portal_output  CC=11  out:8
  imgl.capture_provenance  [5 funcs]
    _correlate_os_windows  CC=10  out:13
    capture_meta_path  CC=1  out:2
    enrich_scene_provenance  CC=4  out:4
    load_capture_meta  CC=4  out:5
    save_capture_meta  CC=1  out:7
  imgl.catalog  [3 funcs]
    _truncate  CC=2  out:3
    build_interactive_catalog  CC=3  out:3
    format_catalog_table  CC=8  out:10
  imgl.catalog_filter  [7 funcs]
    _element_score  CC=9  out:5
    _keep_element  CC=7  out:6
    _renumber  CC=2  out:4
    _replace_index_in_uri  CC=1  out:0
    _text_quality_check  CC=10  out:8
    _window_score  CC=5  out:1
    filter_catalog  CC=8  out:7
  imgl.catalog_heuristic  [2 funcs]
    _find_window  CC=2  out:1
    build_heuristic_catalog  CC=10  out:9
  imgl.classify.gui_heuristics  [1 funcs]
    classify_scene_elements  CC=11  out:9
  imgl.cli  [25 funcs]
    _add_common_args  CC=1  out:5
    _apply_config_overrides  CC=2  out:1
    _check_blank_before_analyze  CC=5  out:7
    _handle_analyze  CC=1  out:3
    _handle_annotate  CC=4  out:14
    _handle_capture  CC=13  out:22
    _handle_diagnose  CC=4  out:17
    _handle_doctor  CC=2  out:5
    _handle_execute  CC=4  out:7
    _handle_find  CC=6  out:11
  imgl.control  [16 funcs]
    _control_packages_present  CC=2  out:4
    _require_nlp2imgl  CC=4  out:4
    _try_fallback_screen_png  CC=5  out:14
    _try_vdisplay_fallback  CC=5  out:6
    _vql_cache_paths  CC=1  out:2
    capture_interactive  CC=16  out:28
    clear_ocr_cache  CC=1  out:1
    default_image_path  CC=3  out:5
    default_window  CC=3  out:2
    run_doctor  CC=7  out:11
  imgl.coords  [1 funcs]
    scale_scene_to_screen  CC=6  out:29
  imgl.detect.img2vql_bridge  [1 funcs]
    detect_ui_merged  CC=4  out:2
  imgl.diagnose  [8 funcs]
    _diagnose_fallback  CC=8  out:14
    _diagnose_with_img2nl  CC=2  out:5
    _has_ui_signals  CC=7  out:11
    _scene_class  CC=2  out:6
    content_summary  CC=6  out:6
    diagnose_content  CC=3  out:7
    img2nl_available  CC=2  out:0
    worth_analyzing  CC=6  out:5
  imgl.execute  [4 funcs]
    _display_mismatch_warning  CC=8  out:8
    _normalize_keys  CC=9  out:12
    execute_action  CC=13  out:27
    execute_keys  CC=5  out:8
  imgl.export.annotate_export  [4 funcs]
    default_annotated_path  CC=3  out:3
    open_image  CC=4  out:5
    write_annotated_image  CC=1  out:5
    write_window_preview_images  CC=3  out:20
  imgl.export.html_export  [1 funcs]
    scene_to_html  CC=4  out:9
  imgl.export.json_export  [2 funcs]
    scene_from_json  CC=2  out:3
    scene_to_json  CC=1  out:2
  imgl.export.svg_export  [1 funcs]
    scene_to_svg  CC=4  out:9
  imgl.export.vql_adapter  [2 funcs]
    scene_to_vql_json  CC=1  out:2
    write_vql_program  CC=4  out:10
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
  imgl.geometry  [3 funcs]
    bbox_distance  CC=1  out:0
    center_in  CC=2  out:1
    iou  CC=3  out:7
  imgl.installs  [9 funcs]
    _auto_install_vdisplay_enabled  CC=1  out:3
    _pip_install_editable  CC=2  out:2
    _repo_root  CC=2  out:6
    ensure_vdisplay  CC=5  out:5
    install_control  CC=1  out:8
    install_img2nl  CC=2  out:5
    install_vdisplay  CC=2  out:5
    install_vql  CC=1  out:4
    vdisplay_available  CC=2  out:0
  imgl.interact  [21 funcs]
    _annotate_catalog  CC=6  out:8
    _attach_image_path  CC=1  out:1
    _build_session_catalog  CC=2  out:1
    _click_by_element_id  CC=4  out:2
    _export_window_previews  CC=4  out:6
    _handle_resolved_shell_action  CC=11  out:27
    _handle_window_phase_prompt  CC=9  out:21
    _prepare_interactive_session  CC=4  out:16
    _print_actions_phase_hints  CC=9  out:12
    _print_catalog_banner  CC=8  out:10
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
  imgl.nlp2uri  [7 funcs]
    _delegate_vql_nlp2uri  CC=5  out:6
    _find_catalog_by_text  CC=9  out:3
    _find_catalog_input  CC=9  out:4
    _match_catalog_action  CC=8  out:4
    _resolve_click_intent  CC=3  out:7
    _resolve_type_intent  CC=12  out:8
    prompt_to_imgl_uri  CC=15  out:24
  imgl.ocr  [1 funcs]
    get_ocr_backend  CC=2  out:2
  imgl.paths  [2 funcs]
    resolve_image_path  CC=5  out:11
    resolve_image_path_optional  CC=3  out:2
  imgl.pipeline  [3 funcs]
    _content_metadata  CC=1  out:6
    _count_roles  CC=4  out:2
    analyze  CC=11  out:22
  imgl.preprocess  [2 funcs]
    load_image  CC=2  out:8
    preprocess  CC=3  out:8
  imgl.scene_cache  [4 funcs]
    load_cached_scene  CC=5  out:10
    load_or_analyze  CC=5  out:7
    save_scene_cache  CC=1  out:3
    scene_cache_path  CC=2  out:3
  imgl.terminal_md  [11 funcs]
    _c  CC=1  out:1
    _color_yaml_value  CC=6  out:12
    _highlight_bash_line  CC=10  out:19
    _highlight_inline  CC=1  out:8
    _highlight_yaml_line  CC=3  out:8
    _render_fence_line  CC=3  out:3
    _render_normal_line  CC=6  out:17
    _verdict_color  CC=1  out:3
    colorize_markdown  CC=11  out:15
    print_report  CC=3  out:3
  imgl.uri  [7 funcs]
    _imgl_uri  CC=5  out:3
    uri_for_imgl_action  CC=1  out:1
    uri_for_imgl_analyze  CC=2  out:1
    uri_for_imgl_annotate  CC=2  out:1
    uri_for_imgl_click  CC=5  out:1
    uri_for_imgl_list  CC=1  out:1
    uri_for_imgl_type  CC=5  out:1
  imgl.vdisplay_bridge  [3 funcs]
    build_window_control_report  CC=10  out:23
    correlate_windows  CC=7  out:17
    list_os_windows  CC=3  out:3
  imgl.vdisplay_context  [3 funcs]
    _metadata_from_context  CC=8  out:12
    enrich_scene_from_vdisplay  CC=1  out:2
    from_vdisplay_context  CC=10  out:20
  imgl.vision_ops  [5 funcs]
    _crop_png_region  CC=1  out:7
    _png_to_gray_array  CC=1  out:5
    diff_png_bytes  CC=11  out:13
    match_template_png  CC=11  out:29
    template_available  CC=2  out:0
  imgl.window_scope  [29 funcs]
    _best_vertical_split  CC=12  out:10
    _collect_elements  CC=2  out:2
    _detect_layout_mode  CC=12  out:16
    _element_gap_gutters  CC=6  out:9
    _guess_window_title  CC=6  out:6
    _image_gutter_candidates  CC=14  out:19
    _regions_from_balanced_gutters  CC=10  out:14
    _safe_filename  CC=6  out:5
    _score_gutter_candidate  CC=10  out:4
    _shift_elements  CC=2  out:5
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
  packages.dsl2imgl.src.dsl2imgl.grammar  [16 funcs]
    _apply_image_window_flags  CC=3  out:2
    _parse_actions  CC=4  out:1
    _parse_agent  CC=3  out:7
    _parse_analyze  CC=5  out:2
    _parse_capture  CC=5  out:3
    _parse_click  CC=3  out:5
    _parse_execute  CC=1  out:3
    _parse_interaction_verb  CC=5  out:8
    _parse_key  CC=5  out:3
    _parse_resolve  CC=1  out:2
  packages.dsl2imgl.src.dsl2imgl.handlers.runtime  [7 funcs]
    _build_interact_session  CC=4  out:12
    _run_prompt_act  CC=8  out:15
    handle_actions  CC=4  out:11
    handle_analyze  CC=4  out:10
    handle_capture  CC=5  out:21
    handle_execute  CC=14  out:35
    handle_resolve  CC=7  out:14
  packages.dsl2imgl.src.dsl2imgl.pb_codec  [31 funcs]
    _assign_execute_flag  CC=1  out:2
    _assign_optional_str  CC=2  out:3
    _dict_actions_body  CC=3  out:1
    _dict_agent_body  CC=2  out:3
    _dict_analyze_body  CC=3  out:2
    _dict_capture_body  CC=2  out:1
    _dict_click_body  CC=2  out:5
    _dict_execute_body  CC=1  out:3
    _dict_execute_flag  CC=2  out:0
    _dict_key_body  CC=2  out:3
  packages.dsl2imgl.src.dsl2imgl.schema_registry  [4 funcs]
    _load_schemas  CC=4  out:11
    all_verbs  CC=1  out:3
    schema_for_verb  CC=2  out:4
    validate_schemas  CC=3  out:6
  packages.mcp2imgl.src.mcp2imgl.cli  [1 funcs]
    main  CC=2  out:5
  packages.mcp2imgl.src.mcp2imgl.server  [1 funcs]
    run_stdio  CC=2  out:12
  packages.nlp2imgl.src.nlp2imgl.cli  [1 funcs]
    main  CC=1  out:3
  packages.nlp2imgl.src.nlp2imgl.cli_commands  [5 funcs]
    _print_apply_payload  CC=3  out:7
    output_format  CC=1  out:1
    run_apply  CC=6  out:8
    run_doctor  CC=6  out:13
    run_to_dsl  CC=1  out:2
  packages.nlp2imgl.src.nlp2imgl.cli_parser  [1 funcs]
    build_parser  CC=1  out:24
  packages.nlp2imgl.src.nlp2imgl.control  [6 funcs]
    _blocked_capture_response  CC=1  out:1
    _result_to_dict  CC=4  out:13
    apply_nl_with_diag  CC=17  out:16
    default_image_path  CC=3  out:5
    default_window  CC=3  out:2
    doctor_capture  CC=2  out:4
  packages.nlp2imgl.src.nlp2imgl.to_dsl  [4 funcs]
    _dispatch_dsl_command  CC=11  out:16
    apply_nl  CC=5  out:7
    to_dsl  CC=5  out:4
    use_llm_enabled  CC=5  out:7
  packages.rest2imgl.src.rest2imgl.app  [1 funcs]
    create_app  CC=1  out:36
  packages.rest2imgl.src.rest2imgl.cli  [1 funcs]
    main  CC=2  out:8
  packages.uri2imgl.src.uri2imgl.cli  [1 funcs]
    main  CC=4  out:15
  packages.uri2imgl.src.uri2imgl.decode  [3 funcs]
    _dsl_click  CC=4  out:2
    _dsl_type  CC=4  out:3
    uri_to_dsl  CC=12  out:13

EDGES:
  packages.rest2imgl.src.rest2imgl.cli.main → packages.rest2imgl.src.rest2imgl.app.create_app
  packages.cli2imgl.src.cli2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.cli2imgl.src.cli2imgl.cli.main → packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl
  packages.uri2imgl.src.uri2imgl.cli.main → packages.dsl2imgl.src.dsl2imgl.bus.dispatch
  packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl → packages.uri2imgl.src.uri2imgl.decode._dsl_click
  packages.uri2imgl.src.uri2imgl.decode.uri_to_dsl → packages.uri2imgl.src.uri2imgl.decode._dsl_type
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
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_capture_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_analyze_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_actions_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_resolve_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._set_agent_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._assign_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_capture_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_analyze_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_actions_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_resolve_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_click_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_type_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_key_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_execute_flag
  packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_agent_body → packages.dsl2imgl.src.dsl2imgl.pb_codec._dict_optional_str
  packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope → packages.dsl2imgl.src.dsl2imgl.pb_codec._set_body
  packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf → packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 126f 142298L | python:88,json:14,yaml:7,toml:7,shell:7,proto:2 | 2026-06-25
# generated in 0.04s
# CC̅=4.6 | critical:12/588 | dups:0 | cycles:0

HEALTH[12]:
  🟡 CC    apply_nl_with_diag CC=17 (limit:15)
  🟡 CC    prompt_to_imgl_uri CC=15 (limit:15)
  🟡 CC    _resolve_click CC=15 (limit:15)
  🟡 CC    capture_screen CC=20 (limit:15)
  🟡 CC    smart_capture CC=17 (limit:15)
  🟡 CC    capture_interactive CC=16 (limit:15)
  🟡 CC    scene_to_actuation_layers CC=15 (limit:15)
  🟡 CC    act CC=18 (limit:15)
  🟡 CC    _process_window_elements CC=17 (limit:15)
  🟡 CC    _derive_current_next CC=19 (limit:15)
  🟡 CC    normalize_actuation_element CC=15 (limit:15)
  🟡 CC    scene_to_vql CC=16 (limit:15)

REFACTOR[1]:
  1. split 12 high-CC methods  (CC>15)

PIPELINES[135]:
  [1] Src [main]: main → create_app → apply_nl → to_dsl → ...(1 more)
      PURITY: 100% pure
  [2] Src [main]: main → dispatch → _run_handler
      PURITY: 100% pure
  [3] Src [main]: main → uri_to_dsl → _dsl_click
      PURITY: 100% pure
  [4] Src [main]: main → run_stdio → to_dsl → _dispatch_dsl_command
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
  [15] Src [_set_capture_body]: _set_capture_body → _assign_optional_str
      PURITY: 100% pure
  [16] Src [_set_analyze_body]: _set_analyze_body → _assign_optional_str
      PURITY: 100% pure
  [17] Src [_set_actions_body]: _set_actions_body → _assign_optional_str
      PURITY: 100% pure
  [18] Src [_set_resolve_body]: _set_resolve_body → _assign_optional_str
      PURITY: 100% pure
  [19] Src [_set_click_body]: _set_click_body → _assign_optional_str
      PURITY: 100% pure
  [20] Src [_set_type_body]: _set_type_body → _assign_optional_str
      PURITY: 100% pure
  [21] Src [_set_key_body]: _set_key_body → _assign_optional_str
      PURITY: 100% pure
  [22] Src [_set_execute_body]: _set_execute_body → _assign_optional_str
      PURITY: 100% pure
  [23] Src [_set_agent_body]: _set_agent_body → _assign_optional_str
      PURITY: 100% pure
  [24] Src [_dict_capture_body]: _dict_capture_body → _dict_optional_str
      PURITY: 100% pure
  [25] Src [_dict_analyze_body]: _dict_analyze_body → _dict_optional_str
      PURITY: 100% pure
  [26] Src [_dict_actions_body]: _dict_actions_body → _dict_optional_str
      PURITY: 100% pure
  [27] Src [_dict_resolve_body]: _dict_resolve_body → _dict_optional_str
      PURITY: 100% pure
  [28] Src [_dict_click_body]: _dict_click_body → _dict_optional_str
      PURITY: 100% pure
  [29] Src [_dict_type_body]: _dict_type_body → _dict_optional_str
      PURITY: 100% pure
  [30] Src [_dict_key_body]: _dict_key_body → _dict_optional_str
      PURITY: 100% pure
  [31] Src [_dict_execute_body]: _dict_execute_body → _dict_optional_str
      PURITY: 100% pure
  [32] Src [_dict_agent_body]: _dict_agent_body → _dict_optional_str
      PURITY: 100% pure
  [33] Src [encode_text_to_protobuf]: encode_text_to_protobuf → parse_line → split_command
      PURITY: 100% pure
  [34] Src [decode_protobuf_to_text]: decode_protobuf_to_text → to_text
      PURITY: 100% pure
  [35] Src [all_verbs]: all_verbs → _load_schemas
      PURITY: 100% pure
  [36] Src [validate_schemas]: validate_schemas → _load_schemas
      PURITY: 100% pure
  [37] Src [_parse_capture]: _parse_capture → pick_flag
      PURITY: 100% pure
  [38] Src [_parse_analyze]: _parse_analyze → pick_flag
      PURITY: 100% pure
  [39] Src [_parse_actions]: _parse_actions → pick_flag
      PURITY: 100% pure
  [40] Src [_parse_resolve]: _parse_resolve → _strip_prompt_tokens
      PURITY: 100% pure
  [41] Src [_parse_interaction_verb]: _parse_interaction_verb → _apply_image_window_flags → pick_flag
      PURITY: 100% pure
  [42] Src [_parse_agent]: _parse_agent → _apply_image_window_flags → pick_flag
      PURITY: 100% pure
  [43] Src [envelope_to_json]: envelope_to_json → validate_payload → schema_for_verb → _load_schemas
      PURITY: 100% pure
  [44] Src [roundtrip_text]: roundtrip_text → parse_text → parse_line → split_command
      PURITY: 100% pure
  [45] Src [to_json]: to_json
      PURITY: 100% pure
  [46] Src [handle_health]: handle_health
      PURITY: 100% pure
  [47] Src [handle_capture]: handle_capture → capture_screen → default_capture_path
      PURITY: 100% pure
  [48] Src [handle_analyze]: handle_analyze → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure
  [49] Src [handle_actions]: handle_actions → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure
  [50] Src [handle_resolve]: handle_resolve → _build_interact_session → load_or_analyze → analyze → ...(3 more)
      PURITY: 100% pure

LAYERS:
  examples/                       CC̄=7.0    ←in:0  →out:0
  │ demo-nlp2uri                79L  0C    1m  CC=7      ←0
  │ demo-agent-loop.sh          48L  0C    0m  CC=0.0    ←0
  │ demo-windows.sh             23L  0C    0m  CC=0.0    ←0
  │ demo-github.sh              22L  0C    0m  CC=0.0    ←0
  │ img2nl-vql-flow.sh          10L  0C    0m  CC=0.0    ←0
  │
  imgl/                           CC̄=4.9    ←in:69  →out:39  !! split
  │ !! cli                       1003L  0C   26m  CC=13     ←0
  │ !! interact                   722L  1C   22m  CC=15     ←4
  │ !! window_scope               703L  1C   30m  CC=14     ←10
  │ !! capture                    552L  2C   30m  CC=20     ←4
  │ !! autodiag                   549L  0C   34m  CC=19     ←5
  │ !! llm_catalog                521L  0C   16m  CC=14     ←4
  │ !! session                    440L  5C   20m  CC=18     ←0
  │ local                      381L  1C   21m  CC=14     ←0
  │ !! vql_adapter                366L  0C   14m  CC=16     ←4
  │ !! control                    360L  0C   18m  CC=17     ←1
  │ annotate_export            299L  0C   14m  CC=8      ←3
  │ !! nlp2uri                    293L  1C    8m  CC=15     ←4
  │ app                        286L  6C    1m  CC=4      ←0
  │ actions                    281L  4C   17m  CC=14     ←3
  │ vision_ops                 277L  2C    9m  CC=11     ←0
  │ vdisplay_bridge            267L  0C   14m  CC=12     ←3
  │ !! gui_heuristics             266L  0C   10m  CC=17     ←1
  │ !! targets                    261L  0C   14m  CC=15     ←0
  │ catalog_heuristic          256L  0C    6m  CC=13     ←2
  │ diagnose                   247L  1C   10m  CC=10     ←5
  │ terminal_md                213L  0C   11m  CC=11     ←2
  │ execute                    205L  1C    8m  CC=13     ←3
  │ types                      170L  5C   10m  CC=5      ←0
  │ freshness                  151L  0C    9m  CC=5      ←3
  │ html_export                149L  0C    7m  CC=8      ←1
  │ agent                      142L  0C    5m  CC=11     ←1
  │ catalog_filter             139L  0C    7m  CC=10     ←2
  │ svg_export                 137L  0C    7m  CC=4      ←1
  │ installs                   125L  0C    9m  CC=5      ←4
  │ !! actuation_layers           122L  0C    7m  CC=15     ←1
  │ pipeline                   119L  0C    3m  CC=11     ←5
  │ uri                        118L  0C    7m  CC=5      ←4
  │ capture_provenance         114L  0C    5m  CC=10     ←3
  │ layout                     108L  0C    6m  CC=10     ←2
  │ rectangles                  96L  0C    5m  CC=14     ←1
  │ tesseract                   94L  1C    2m  CC=13     ←0
  │ catalog                     91L  0C    3m  CC=8      ←4
  │ __init__                    86L  0C    0m  CC=0.0    ←0
  │ vdisplay_context            80L  0C    3m  CC=10     ←0
  │ coords                      70L  0C    1m  CC=6      ←1
  │ img2vql_bridge              64L  0C    4m  CC=4      ←1
  │ scene_cache                 63L  0C    4m  CC=5      ←5
  │ preprocess                  63L  1C    2m  CC=3      ←1
  │ thumbs                      55L  0C    3m  CC=3      ←1
  │ catalog_types               46L  1C    1m  CC=1      ←0
  │ __init__                    42L  0C    0m  CC=0.0    ←0
  │ paths                       41L  0C    2m  CC=5      ←6
  │ geometry                    37L  0C    4m  CC=3      ←8
  │ lang                        32L  0C    2m  CC=6      ←1
  │ config                      23L  1C    0m  CC=0.0    ←0
  │ json_export                 22L  0C    2m  CC=2      ←3
  │ _escape                     19L  0C    2m  CC=1      ←2
  │ base                        14L  1C    1m  CC=1      ←0
  │ __init__                    12L  0C    1m  CC=2      ←1
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ __init__                    10L  0C    1m  CC=1      ←0
  │ __main__                     6L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │
  packages/                       CC̄=3.3    ←in:0  →out:0
  │ pb_codec                   284L  0C   32m  CC=5      ←3
  │ runtime                    234L  0C    8m  CC=14     ←0
  │ grammar                    190L  0C   16m  CC=10     ←3
  │ events                     168L  2C    8m  CC=6      ←0
  │ !! control                    150L  0C    6m  CC=17     ←4
  │ app                        125L  2C    1m  CC=1      ←2
  │ bus                        110L  0C    5m  CC=10     ←6
  │ to_dsl                     103L  0C    4m  CC=11     ←5
  │ command.proto               83L  0C    0m  CC=0.0    ←0
  │ cli_commands                71L  0C    5m  CC=6      ←1
  │ codec                       57L  0C    7m  CC=2      ←1
  │ command_pb2                 56L  0C    0m  CC=0.0    ←0
  │ cli                         46L  0C    1m  CC=9      ←0
  │ schema_registry             44L  0C    4m  CC=4      ←1
  │ decode                      43L  0C    3m  CC=12     ←1
  │ result_pb2                  39L  0C    0m  CC=0.0    ←0
  │ cli_parser                  37L  0C    1m  CC=1      ←1
  │ cli                         36L  0C    1m  CC=4      ←0
  │ server                      35L  0C    1m  CC=2      ←1
  │ cli                         34L  0C    1m  CC=6      ←0
  │ result                      34L  1C    2m  CC=1      ←0
  │ pyproject.toml              27L  0C    0m  CC=0.0    ←0
  │ cli                         26L  0C    1m  CC=2      ←0
  │ result.proto                23L  0C    0m  CC=0.0    ←0
  │ cli                         22L  0C    1m  CC=2      ←0
  │ cli                         22L  0C    1m  CC=1      ←0
  │ pyproject.toml              21L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              19L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ pyproject.toml              16L  0C    0m  CC=0.0    ←0
  │ type.schema.json            14L  0C    0m  CC=0.0    ←0
  │ click.schema.json           14L  0C    0m  CC=0.0    ←0
  │ capture.schema.json         13L  0C    0m  CC=0.0    ←0
  │ execute.schema.json         13L  0C    0m  CC=0.0    ←0
  │ agent.schema.json           13L  0C    0m  CC=0.0    ←0
  │ analyze.schema.json         13L  0C    0m  CC=0.0    ←0
  │ key.schema.json             13L  0C    0m  CC=0.0    ←0
  │ resolve.schema.json         12L  0C    0m  CC=0.0    ←0
  │ actions.schema.json         12L  0C    0m  CC=0.0    ←0
  │ health.schema.json           9L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ generate-proto.sh            6L  0C    0m  CC=0.0    ←0
  │ engine                       5L  0C    0m  CC=0.0    ←0
  │ __init__                     4L  0C    0m  CC=0.0    ←0
  │ __init__                     3L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! layout.vql.json          63208L  0C    0m  CC=0.0    ←0
  │ !! screen.vql.json          51347L  0C    0m  CC=0.0    ←0
  │ !! screen.vql.imgl.json     11260L  0C    0m  CC=0.0    ←0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  527L  0C    0m  CC=0.0    ←0
  │ Makefile                   148L  0C    0m  CC=0.0    ←0
  │ koru.yaml                  141L  0C    0m  CC=0.0    ←0
  │ pyproject.toml             103L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ layout.vql.imgl.json        75L  0C    0m  CC=0.0    ←0
  │ project.sh                  59L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-api-smoke.testql.toon.yaml    39L  0C    0m  CC=0.0    ←0
  │ generated-api-integration.testql.toon.yaml    18L  0C    0m  CC=0.0    ←0
  │ generated-from-pytests.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │

COUPLING:
                                    imgl         imgl.export   packages.nlp2imgl   packages.dsl2imgl            imgl.web       imgl.classify  packages.rest2imgl         imgl.detect    examples.scripts   packages.cli2imgl   packages.mcp2imgl   packages.uri2imgl
                imgl                  ──                  28                   7                 ←11                 ←14                   1                   1                   2                  ←5                                                              hub
         imgl.export                   7                  ──                                      ←1                  ←2                                                                                                                                              hub
   packages.nlp2imgl                  17                                      ──                   3                                                          ←5                                                          ←2                  ←2                      hub
   packages.dsl2imgl                  11                   1                  ←3                  ──                                                          ←4                                                          ←1                  ←1                  ←1  hub
            imgl.web                  14                   2                                                          ──                                                                                                                                              !! fan-out
       imgl.classify                   9                                                                                                  ──                                                                                                                          !! fan-out
  packages.rest2imgl                  ←1                                       5                   4                                                          ──                                                                                                      !! fan-out
         imgl.detect                   6                                                                                                                                          ──                                                                                
    examples.scripts                   5                                                                                                                                                              ──                                                            
   packages.cli2imgl                                                           2                   1                                                                                                                      ──                                        
   packages.mcp2imgl                                                           2                   1                                                                                                                                          ──                    
   packages.uri2imgl                                                                               1                                                                                                                                                              ──
  CYCLES: none
  HUB: imgl.export/ (fan-in=31)
  HUB: packages.dsl2imgl/ (fan-in=10)
  HUB: imgl/ (fan-in=69)
  HUB: packages.nlp2imgl/ (fan-in=16)
  SMELL: imgl.classify/ fan-out=9 → split needed
  SMELL: packages.dsl2imgl/ fan-out=12 → split needed
  SMELL: imgl/ fan-out=39 → split needed
  SMELL: packages.rest2imgl/ fan-out=9 → split needed
  SMELL: packages.nlp2imgl/ fan-out=20 → split needed
  SMELL: imgl.web/ fan-out=16 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 11 groups | 88f 13489L | 2026-06-24

SUMMARY:
  files_scanned: 88
  total_lines:   13489
  dup_groups:    11
  dup_fragments: 23
  saved_lines:   86
  scan_ms:       2699

HOTSPOTS[7] (files with most duplication):
  imgl/installs.py  dup=34L  groups=3  frags=4  (0.3%)
  imgl/export/html_export.py  dup=28L  groups=2  frags=2  (0.2%)
  imgl/control.py  dup=19L  groups=3  frags=4  (0.1%)
  imgl/export/svg_export.py  dup=17L  groups=2  frags=2  (0.1%)
  imgl/targets.py  dup=12L  groups=1  frags=2  (0.1%)
  packages/dsl2imgl/src/dsl2imgl/pb_codec.py  dup=10L  groups=1  frags=2  (0.1%)
  imgl/detect/img2vql_bridge.py  dup=7L  groups=1  frags=1  (0.1%)

DUPLICATES[11] (ranked by impact):
  [49d1d03e6ce392a1]   STRU  _base_css  L=21 N=2 saved=21 sim=1.00
      imgl/export/html_export.py:75-95  (_base_css)
      imgl/export/svg_export.py:76-85  (_svg_css)
  [5843dfdd9fc8bd2f]   STRU  img2vql_available  L=7 N=3 saved=14 sim=1.00
      imgl/detect/img2vql_bridge.py:18-24  (img2vql_available)
      imgl/diagnose.py:16-22  (img2nl_available)
      imgl/installs.py:21-27  (vdisplay_available)
  [3e7a5c4c9a268921]   STRU  install_img2nl  L=10 N=2 saved=10 sim=1.00
      imgl/installs.py:58-67  (install_img2nl)
      imgl/installs.py:70-83  (install_vdisplay)
  [00c76eba96672ce9]   EXAC  _default_title  L=7 N=2 saved=7 sim=1.00
      imgl/export/html_export.py:56-62  (_default_title)
      imgl/export/svg_export.py:56-62  (_default_title)
  [d82a12d006aec7c6]   EXAC  default_window  L=6 N=2 saved=6 sim=1.00
      imgl/control.py:23-28  (default_window)
      packages/nlp2imgl/src/nlp2imgl/control.py:21-26  (default_window)
  [af1e81a142ce15c1]   STRU  _bbox_center_x  L=6 N=2 saved=6 sim=1.00
      imgl/targets.py:15-20  (_bbox_center_x)
      imgl/targets.py:23-28  (_bbox_center_y)
  [e4a985e7f83fe868]   STRU  _truncate  L=5 N=2 saved=5 sim=1.00
      imgl/catalog.py:87-91  (_truncate)
      imgl/export/annotate_export.py:231-235  (_short_hint_text)
  [f81040e23b7ff781]   STRU  _vql_cache_paths  L=5 N=2 saved=5 sim=1.00
      imgl/control.py:31-35  (_vql_cache_paths)
      imgl/freshness.py:41-45  (vql_cache_paths)
  [684ba64a9784557d]   STRU  _set_key_body  L=5 N=2 saved=5 sim=1.00
      packages/dsl2imgl/src/dsl2imgl/pb_codec.py:76-80  (_set_key_body)
      packages/dsl2imgl/src/dsl2imgl/pb_codec.py:83-87  (_set_execute_body)
  [86c2b27187305f83]   STRU  install_img2nl  L=4 N=2 saved=4 sim=1.00
      imgl/control.py:335-338  (install_img2nl)
      imgl/control.py:341-344  (install_vdisplay)
  [2d7b9210c1b65241]   STRU  _prefer_mirror  L=3 N=2 saved=3 sim=1.00
      imgl/capture.py:50-52  (_prefer_mirror)
      imgl/installs.py:30-32  (_auto_install_vdisplay_enabled)

REFACTOR[11] (ranked by priority):
  [1] ○ extract_function   → imgl/export/utils/_base_css.py
      WHY: 2 occurrences of 21-line block across 2 files — saves 21 lines
      FILES: imgl/export/html_export.py, imgl/export/svg_export.py
  [2] ○ extract_function   → imgl/utils/img2vql_available.py
      WHY: 3 occurrences of 7-line block across 3 files — saves 14 lines
      FILES: imgl/detect/img2vql_bridge.py, imgl/diagnose.py, imgl/installs.py
  [3] ○ extract_function   → imgl/utils/install_img2nl.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: imgl/installs.py
  [4] ○ extract_function   → imgl/export/utils/_default_title.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: imgl/export/html_export.py, imgl/export/svg_export.py
  [5] ○ extract_function   → utils/default_window.py
      WHY: 2 occurrences of 6-line block across 2 files — saves 6 lines
      FILES: imgl/control.py, packages/nlp2imgl/src/nlp2imgl/control.py
  [6] ○ extract_function   → imgl/utils/_bbox_center_x.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: imgl/targets.py
  [7] ○ extract_function   → imgl/utils/_truncate.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: imgl/catalog.py, imgl/export/annotate_export.py
  [8] ○ extract_function   → imgl/utils/_vql_cache_paths.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: imgl/control.py, imgl/freshness.py
  [9] ○ extract_function   → packages/dsl2imgl/src/dsl2imgl/utils/_set_key_body.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: packages/dsl2imgl/src/dsl2imgl/pb_codec.py
  [10] ○ extract_function   → imgl/utils/install_img2nl.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: imgl/control.py
  [11] ○ extract_function   → imgl/utils/_prefer_mirror.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: imgl/capture.py, imgl/installs.py

QUICK_WINS[6] (low risk, high savings — do first):
  [1] extract_function   saved=21L  → imgl/export/utils/_base_css.py
      FILES: html_export.py, svg_export.py
  [2] extract_function   saved=14L  → imgl/utils/img2vql_available.py
      FILES: img2vql_bridge.py, diagnose.py, installs.py
  [3] extract_function   saved=10L  → imgl/utils/install_img2nl.py
      FILES: installs.py
  [4] extract_function   saved=7L  → imgl/export/utils/_default_title.py
      FILES: html_export.py, svg_export.py
  [5] extract_function   saved=6L  → utils/default_window.py
      FILES: control.py, control.py
  [6] extract_function   saved=6L  → imgl/utils/_bbox_center_x.py
      FILES: targets.py

DEPENDENCY_RISK[1] (duplicates spanning multiple packages):
  default_window  packages=2  files=2
      imgl/control.py
      packages/nlp2imgl/src/nlp2imgl/control.py

EFFORT_ESTIMATE (total ≈ 3.1h):
  medium _base_css                           saved=21L  ~42min
  easy   img2vql_available                   saved=14L  ~28min
  easy   install_img2nl                      saved=10L  ~20min
  easy   _default_title                      saved=7L  ~14min
  easy   default_window                      saved=6L  ~24min
  easy   _bbox_center_x                      saved=6L  ~12min
  easy   _truncate                           saved=5L  ~10min
  easy   _vql_cache_paths                    saved=5L  ~10min
  easy   _set_key_body                       saved=5L  ~10min
  easy   install_img2nl                      saved=4L  ~8min
  ... +1 more (~6min)

METRICS-TARGET:
  dup_groups:  11 → 0
  saved_lines: 86 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 587 func | 73f | 2026-06-25
# generated in 0.00s

NEXT[10] (ranked by impact):
  [1] !  SPLIT-FUNC      capture_screen  CC=20  fan=19
      WHY: CC=20 exceeds 15
      EFFORT: ~1h  IMPACT: 380

  [2] !  SPLIT-FUNC      capture_interactive  CC=16  fan=20
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 320

  [3] !  SPLIT-FUNC      smart_capture  CC=17  fan=17
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 289

  [4] !  SPLIT-FUNC      prompt_to_imgl_uri  CC=15  fan=19
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 285

  [5] !  SPLIT-FUNC      scene_to_vql  CC=16  fan=17
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 272

  [6] !  SPLIT-FUNC      _process_window_elements  CC=17  fan=14
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 238

  [7] !  SPLIT-FUNC      WebSession.act  CC=18  fan=13
      WHY: CC=18 exceeds 15
      EFFORT: ~1h  IMPACT: 234

  [8] !  SPLIT-FUNC      apply_nl_with_diag  CC=17  fan=13
      WHY: CC=17 exceeds 15
      EFFORT: ~1h  IMPACT: 221

  [9] !  SPLIT-FUNC      _derive_current_next  CC=19  fan=10
      WHY: CC=19 exceeds 15
      EFFORT: ~1h  IMPACT: 190

  [10] !! SPLIT           layout.vql.json
      WHY: 63208L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting layout.vql.json may break 0 import paths
  ⚠ Splitting screen.vql.json may break 0 import paths
  ⚠ Splitting screen.vql.imgl.json may break 0 import paths

METRICS-TARGET:
  CC̄:          4.6 → ≤3.2
  max-CC:      20 → ≤10
  god-modules: 11 → 0
  high-CC(≥15): 12 → ≤6
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
  prev CC̄=4.6 → now CC̄=4.6
```

## Intent

Image to Layout — screenshot OCR and semantic UI reconstruction
