# ImgL - Image to Layout — convert screenshots into semantic UI models with OCR text and element bounding boxes.

Image to Layout — screenshot OCR and semantic UI reconstruction

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Interfaces](#interfaces)
- [Workflows](#workflows)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [Deployment](#deployment)
- [Environment Variables (`.env.example`)](#environment-variables-envexample)
- [Release Management (`goal.yaml`)](#release-management-goalyaml)
- [Makefile Targets](#makefile-targets)
- [Code Analysis](#code-analysis)
- [Source Map](#source-map)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Intent](#intent)

## Metadata

- **name**: `imgl`
- **version**: `0.7.2`
- **python_requires**: `>=3.10`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(3), app.doql.less, goal.yaml, .env.example, src(24 mod), project/(3 analysis files)

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

## Interfaces

### CLI Entry Points

- `imgl`

### testql Scenarios

#### `testql-scenarios/generated-api-integration.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-integration.testql.toon.yaml
# SCENARIO: API Integration Tests
# TYPE: api
# GENERATED: true

CONFIG[3]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 30000
  retry_count, 3

API[4]{method, endpoint, expected_status}:
  GET, /health, 200
  GET, /api/v1/status, 200
  POST, /api/v1/test, 201
  GET, /api/v1/docs, 200

ASSERT[2]{field, operator, expected}:
  status, ==, ok
  response_time, <, 1000
```

#### `testql-scenarios/generated-api-smoke.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-api-smoke.testql.toon.yaml
# SCENARIO: Auto-generated API Smoke Tests
# TYPE: api
# GENERATED: true
# DETECTORS: FastAPIDetector, TestEndpointDetector

CONFIG[5]{key, value}:
  base_url, http://localhost:8101
  timeout_ms, 10000
  retry_count, 3
  retry_backoff_ms, 1000
  detected_frameworks, FastAPIDetector, TestEndpointDetector

# Wait for service to be ready
WAIT 1000

# Health check
API GET /api/health 200
ASSERT_STATUS 200

# REST API Endpoints (1 unique)
API[1]{method, endpoint, expected_status}:
  GET, /, 200

# Capture useful values from responses for subsequent tests
# CAPTURE request_id FROM 'headers.x-request-id'
# CAPTURE session_token FROM 'body.token'

ASSERT[2]{field, operator, expected}:
  _status, <, 500
  _status, >=, 200

# Conditional flow for error handling
FLOW[2]{condition, action}:
  _status >= 500, LOG 'Server error detected'
  _status == 429, WAIT 2000  # Rate limit - wait and retry


# Summary by Framework:
#   fastapi: 1 endpoints
```

#### `testql-scenarios/generated-from-pytests.testql.toon.yaml`

```toon markpact:testql path=testql-scenarios/generated-from-pytests.testql.toon.yaml
# SCENARIO: Auto-generated from Python Tests
# TYPE: integration
# GENERATED: true

CONFIG[2]{key, value}:
  base_url, ${api_url:-http://localhost:8101}
  timeout_ms, 10000

# Converted 4 assertions from pytest
ASSERT[4]{field, operator, expected}:
  scene.width, ==, 200
  scene.height, ==, 80
  scene.width, ==, 200
  scene.height, ==, 80
```

## Workflows

## Configuration

```yaml
project:
  name: imgl
  version: 0.7.2
  env: local
```

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

## Deployment

```bash markpact:run
pip install imgl

# development install
pip install -e .[dev]
```

## Environment Variables (`.env.example`)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | OpenRouter API Key (required for real cost calculation) |
| `LLM_MODEL` | `openrouter/qwen/qwen3-coder-next` | Default AI model for cost analysis |

## Release Management (`goal.yaml`)

- **versioning**: `semver`
- **commits**: `conventional` scope=`imgl`
- **changelog**: `keep-a-changelog`
- **build strategies**: `python`, `nodejs`, `rust`
- **version files**: `VERSION`, `pyproject.toml:version`, `imgl/__init__.py:__version__`

## Makefile Targets

- `SHELL`
- `PIP`
- `PY`
- `IMGL_ROOT`
- `help`
- `venv`
- `install`
- `install-dev`
- `install-control`
- `install-full`
- `install-img2nl`
- `install-vdisplay`
- `test`
- `test-imgl`
- `test-dsl2imgl`
- `capture`
- `capture-interactive`
- `verify-capture`
- `windows`
- `doctor`
- `doctor-full`
- `execute`
- `execute-dry`
- `execute-llm`
- `shot`
- `shot-llm`
- `proto`
- `serve-rest`
- `serve-web`
- `demo-key`
- `demo-nl`
- `demo-chat`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# imgl | 113f 13391L | python:99,shell:13,less:1 | 2026-06-09
# stats: 463 func | 38 cls | 113 mod | CC̄=5.1 | critical:53 | cycles:0
# alerts[5]: CC main=44; CC parse_line=44; CC run_interactive_shell=43; CC envelope_to_dict=42; CC _set_body=31
# hotspots[5]: main fan=41; create_app fan=38; run_interactive_shell fan=32; _run_image_command fan=28; _detect_buttons fan=24
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[113]:
  app.doql.less,212
  examples/scripts/demo-agent-loop.sh,38
  examples/scripts/demo-github.sh,22
  examples/scripts/demo-nlp2uri.py,80
  examples/scripts/demo-windows.sh,23
  imgl/__init__.py,52
  imgl/__main__.py,7
  imgl/actions.py,272
  imgl/autodiag.py,407
  imgl/capture.py,212
  imgl/catalog.py,351
  imgl/catalog_filter.py,139
  imgl/classify/__init__.py,6
  imgl/classify/gui_heuristics.py,262
  imgl/cli.py,718
  imgl/config.py,24
  imgl/coords.py,71
  imgl/detect/__init__.py,12
  imgl/detect/img2vql_bridge.py,65
  imgl/detect/local.py,279
  imgl/detect/rectangles.py,97
  imgl/diagnose.py,248
  imgl/execute.py,163
  imgl/export/__init__.py,31
  imgl/export/_escape.py,20
  imgl/export/annotate_export.py,300
  imgl/export/html_export.py,150
  imgl/export/json_export.py,23
  imgl/export/svg_export.py,138
  imgl/export/vql_adapter.py,245
  imgl/freshness.py,152
  imgl/geometry.py,38
  imgl/interact.py,561
  imgl/layout.py,109
  imgl/llm_catalog.py,521
  imgl/nlp2uri.py,283
  imgl/ocr/__init__.py,13
  imgl/ocr/base.py,15
  imgl/ocr/lang.py,33
  imgl/ocr/tesseract.py,95
  imgl/paths.py,42
  imgl/pipeline.py,117
  imgl/preprocess.py,64
  imgl/scene_cache.py,64
  imgl/types.py,171
  imgl/uri.py,119
  imgl/vdisplay_bridge.py,254
  imgl/web/__init__.py,11
  imgl/web/agent.py,153
  imgl/web/app.py,287
  imgl/web/session.py,453
  imgl/web/thumbs.py,56
  imgl/window_scope.py,576
  packages/cli2imgl/src/cli2imgl/cli.py,35
  packages/dsl2imgl/scripts/generate-proto.sh,7
  packages/dsl2imgl/src/dsl2imgl/__init__.py,7
  packages/dsl2imgl/src/dsl2imgl/bus.py,111
  packages/dsl2imgl/src/dsl2imgl/cli.py,47
  packages/dsl2imgl/src/dsl2imgl/codec.py,58
  packages/dsl2imgl/src/dsl2imgl/engine.py,6
  packages/dsl2imgl/src/dsl2imgl/events.py,169
  packages/dsl2imgl/src/dsl2imgl/grammar.py,138
  packages/dsl2imgl/src/dsl2imgl/handlers/__init__.py,2
  packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py,221
  packages/dsl2imgl/src/dsl2imgl/pb_codec.py,241
  packages/dsl2imgl/src/dsl2imgl/result.py,35
  packages/dsl2imgl/src/dsl2imgl/schema_registry.py,45
  packages/dsl2imgl/src/dsl2imgl/v1/__init__.py,2
  packages/dsl2imgl/src/dsl2imgl/v1/command_pb2.py,57
  packages/dsl2imgl/src/dsl2imgl/v1/result_pb2.py,40
  packages/dsl2imgl/tests/test_dsl2imgl.py,38
  packages/dsl2imgl/tests/test_dsl2imgl_phase4.py,71
  packages/mcp2imgl/src/mcp2imgl/cli.py,23
  packages/mcp2imgl/src/mcp2imgl/server.py,36
  packages/nlp2imgl/src/nlp2imgl/__init__.py,5
  packages/nlp2imgl/src/nlp2imgl/cli.py,92
  packages/nlp2imgl/src/nlp2imgl/control.py,151
  packages/nlp2imgl/src/nlp2imgl/to_dsl.py,94
  packages/rest2imgl/src/rest2imgl/app.py,126
  packages/rest2imgl/src/rest2imgl/cli.py,27
  packages/uri2imgl/src/uri2imgl/__init__.py,4
  packages/uri2imgl/src/uri2imgl/cli.py,37
  packages/uri2imgl/src/uri2imgl/decode.py,36
  project.sh,59
  tests/test_actions.py,140
  tests/test_annotate.py,59
  tests/test_autodiag.py,91
  tests/test_capture_paths.py,105
  tests/test_catalog_filter.py,73
  tests/test_catalog_interact.py,200
  tests/test_diagnose.py,147
  tests/test_execute_key.py,17
  tests/test_export.py,218
  tests/test_imgl.py,202
  tests/test_layout_classify.py,176
  tests/test_llm_catalog.py,127
  tests/test_nlp2imgl_control.py,36
  tests/test_nlp2imgl_llm.py,29
  tests/test_nlp2uri_fixes.py,63
  tests/test_ocr_lang.py,17
  tests/test_scene_cache.py,90
  tests/test_vdisplay_bridge.py,51
  tests/test_vql_export.py,106
  tests/test_web.py,121
  tests/test_window_scope.py,198
  tree.sh,2
D:
  examples/scripts/demo-nlp2uri.py:
    e: main
    main()
  imgl/__init__.py:
  imgl/__main__.py:
  imgl/actions.py:
    e: actions,_format_query,_text_matches,_iter_elements,_window_matches,_find_label_for_input,ActionTarget,TypeAction,SceneActions,ElementNotFoundError
    ActionTarget: center(0),click_coords(0),to_click_action(0)  # A resolved UI element that can be clicked or typed into.
    TypeAction: coords(0),to_dict(0)  # Type text into an input field.
    SceneActions: find(1),find_one(1),click(1),type_into(1),list_actions(0)  # Find and interact with elements in a Scene.
    ElementNotFoundError:  # Raised when no element matches the query.
    actions(scene)
    _format_query(element_type)
    _text_matches(value;query)
    _iter_elements(scene)
    _window_matches(window;query)
    _find_label_for_input(scene;input_element;window)
  imgl/autodiag.py:
    e: img2nl_root,img2nl_available,diagnose_capture,build_operation_step,_compact_result,build_execute_report,pick_output_format,render_report,_flag_enabled,should_block_blank_capture,should_block_stale_capture,diagnostics_enabled,_render_markdown,_overall_verdict,_actionable_hints,_compact_features,_scene_class,_parse_coords,_coords_from_action,_parse_typed_text,_parse_keys
    img2nl_root()
    img2nl_available()
    diagnose_capture(image_path)
    build_operation_step(result)
    _compact_result(result)
    build_execute_report()
    pick_output_format(payload;requested)
    render_report(payload;fmt)
    _flag_enabled()
    should_block_blank_capture(capture)
    should_block_stale_capture(capture)
    diagnostics_enabled()
    _render_markdown(report)
    _overall_verdict(capture;operation)
    _actionable_hints(report)
    _compact_features(features)
    _scene_class(diag)
    _parse_coords(message)
    _coords_from_action(action)
    _parse_typed_text(message)
    _parse_keys(message)
  imgl/capture.py:
    e: default_capture_path,_is_wayland,capture_screen,_try_vql_capture,_native_backends,_run_command,_capture_with_grim,_capture_with_gnome_screenshot,_capture_with_scrot,_capture_with_portal,_capture_with_mss,_is_blank_image,capture_status_message,CaptureError,BlankCaptureError
    CaptureError:  # Raised when screen capture fails.
    BlankCaptureError:  # Raised when capture succeeded but image is empty/black.
    default_capture_path(out)
    _is_wayland()
    capture_screen(out)
    _try_vql_capture(path)
    _native_backends()
    _run_command(cmd;path)
    _capture_with_grim(path)
    _capture_with_gnome_screenshot(path)
    _capture_with_scrot(path)
    _capture_with_portal(path)
    _capture_with_mss(path)
    _is_blank_image(path)
    capture_status_message(path)
  imgl/catalog.py:
    e: build_interactive_catalog,format_catalog_table,_window_option,_element_option,_infer_input_label,_find_window,_iter_interactive_elements,_truncate,InteractiveOption
    InteractiveOption: to_dict(0)  # One selectable UI target with mouse/keyboard affordances.
    build_interactive_catalog(scene)
    format_catalog_table(options)
    _window_option(index;window)
    _element_option(index;element)
    _infer_input_label(element;window)
    _find_window(scene;window_id)
    _iter_interactive_elements(scene)
    _truncate(value;max_len)
  imgl/catalog_filter.py:
    e: filter_catalog,_renumber,_replace_index_in_uri,_keep_element,_element_score,_window_score
    filter_catalog(options)
    _renumber(options)
    _replace_index_in_uri(uri;_index)
    _keep_element(option)
    _element_score(option)
    _window_score(option)
  imgl/classify/__init__.py:
  imgl/classify/gui_heuristics.py:
    e: classify_scene_elements,_normalize_confidence,_word_count,_text_or_label,_label_candidates,_match_ocr_to_bbox,_nearest_label,_ocr_inside_frame,_build_inputs
    classify_scene_elements(windows;ocr_boxes;detected;input_frames)
    _normalize_confidence(value)
    _word_count(text)
    _text_or_label(box)
    _label_candidates(window_ocr;used_ocr)
    _match_ocr_to_bbox(bbox;window_ocr;used_ocr)
    _nearest_label(frame;labels;used_ocr)
    _ocr_inside_frame(frame;window_ocr;used_ocr)
    _build_inputs()
  imgl/cli.py:
    e: _add_common_args,build_parser,_write_output,main,_check_blank_before_analyze,_apply_config_overrides,_run_image_command
    _add_common_args(parser)
    build_parser()
    _write_output(content;output)
    main(argv)
    _check_blank_before_analyze(image_path)
    _apply_config_overrides(config;args)
    _run_image_command(args;image_path;config)
  imgl/config.py:
    e: ImglConfig
    ImglConfig:
  imgl/coords.py:
    e: scale_scene_to_screen
    scale_scene_to_screen(scene)
  imgl/detect/__init__.py:
  imgl/detect/img2vql_bridge.py:
    e: img2vql_available,_from_img2vql_dict,detect_with_img2vql,detect_ui_merged
    img2vql_available()
    _from_img2vql_dict(raw)
    detect_with_img2vql(image_path)
    detect_ui_merged(image)
  imgl/detect/local.py:
    e: _hex_color,_avg_color,_iou_xyxy,_detect_titlebar,_flood_rects,_detect_buttons,_detect_panels_simple,_dedupe,detect_ui_elements,DetectedUI
    DetectedUI:
    _hex_color(rgb)
    _avg_color(im;x0;y0;x1;y1)
    _iou_xyxy(a;b)
    _detect_titlebar(im;w;h)
    _flood_rects(mask)
    _detect_buttons(im;w;h)
    _detect_panels_simple(im;w;h)
    _dedupe(elements)
    detect_ui_elements(image)
  imgl/detect/rectangles.py:
    e: detect_input_frames,_find_rectangular_frames,_looks_like_frame,_column_has_edge,_row_has_edge
    detect_input_frames(image)
    _find_rectangular_frames(mask)
    _looks_like_frame(mask;x;y;width;height)
    _column_has_edge(mask;x;y;height)
    _row_has_edge(mask;x;y;width)
  imgl/diagnose.py:
    e: img2nl_available,diagnose_content,worth_analyzing,content_summary,_diagnose_with_img2nl,_diagnose_fallback,_diagnose_pil_fallback,_scene_class,_has_ui_signals,_recommendation,BlankImageError
    BlankImageError:  # Raised when a screenshot has no meaningful UI content.
    img2nl_available()
    diagnose_content(image_path)
    worth_analyzing(diag)
    content_summary(diag)
    _diagnose_with_img2nl(path)
    _diagnose_fallback(path)
    _diagnose_pil_fallback(path)
    _scene_class(diag)
    _has_ui_signals(diag)
    _recommendation(diag)
  imgl/execute.py:
    e: execute_action,_execute_xdotool,_execute_ydotool,execute_keys,_normalize_keys,ExecuteResult
    ExecuteResult: to_dict(0)
    execute_action(action)
    _execute_xdotool(kind;x;y;text)
    _execute_ydotool(kind;x;y;text)
    execute_keys(keys)
    _normalize_keys(keys)
  imgl/export/__init__.py:
  imgl/export/_escape.py:
    e: escape_html,escape_xml
    escape_html(text)
    escape_xml(text)
  imgl/export/annotate_export.py:
    e: default_annotated_path,scene_to_annotated_image,write_annotated_image,write_window_preview_images,write_annotated_images_per_window,open_image,_catalog_relative_to_window,_short_hint_text,_short_hint,_badge_size,_load_fonts,_draw_number_badge,_text_size,_hex_rgba
    default_annotated_path(image_path)
    scene_to_annotated_image(scene;catalog)
    write_annotated_image(scene;catalog;output_path)
    write_window_preview_images(scene;windows;output_dir)
    write_annotated_images_per_window(scene;catalogs)
    open_image(path)
    _catalog_relative_to_window(catalog;origin)
    _short_hint_text(text;max_len)
    _short_hint(option;max_len)
    _badge_size(image_size)
    _load_fonts(image_size)
    _draw_number_badge(draw;text;x;y)
    _text_size(draw;text;font)
    _hex_rgba(hex_color;alpha)
  imgl/export/html_export.py:
    e: scene_to_html,_default_title,_background_layer,_base_css,_render_window,_render_element,_bbox_style
    scene_to_html(scene)
    _default_title(scene)
    _background_layer(scene)
    _base_css()
    _render_window(window)
    _render_element(element)
    _bbox_style(bbox)
  imgl/export/json_export.py:
    e: scene_to_json,scene_from_json
    scene_to_json(scene)
    scene_from_json(payload)
  imgl/export/svg_export.py:
    e: scene_to_svg,_default_title,_background_rect,_svg_css,_render_window_svg,_render_element_svg,_element_css_class
    scene_to_svg(scene)
    _default_title(scene)
    _background_rect(scene)
    _svg_css()
    _render_window_svg(window)
    _render_element_svg(element)
    _element_css_class(element_type)
  imgl/export/vql_adapter.py:
    e: scene_to_vql,scene_to_vql_json,write_vql_program,_grid_layer,_bbox_norm,_location_label,_object_from_bbox,_window_to_object,_element_to_object,_ocr_to_object
    scene_to_vql(scene)
    scene_to_vql_json(scene)
    write_vql_program(scene;path)
    _grid_layer(image_path)
    _bbox_norm(bbox;width;height)
    _location_label(cx;cy;width;height)
    _object_from_bbox()
    _window_to_object(window;width;height)
    _element_to_object(element;width;height)
    _ocr_to_object(box;width;height)
  imgl/freshness.py:
    e: is_valid_png,max_image_age_seconds,capture_sidecar_path,vql_cache_paths,clear_vql_cache,sync_vql_cache_with_image,mark_capture_fresh,image_freshness,verify_capture_updated
    is_valid_png(image)
    max_image_age_seconds()
    capture_sidecar_path(image)
    vql_cache_paths(image)
    clear_vql_cache(image)
    sync_vql_cache_with_image(image)
    mark_capture_fresh(image)
    image_freshness(image_path)
    verify_capture_updated(image;before_mtime)
  imgl/geometry.py:
    e: iou,center_in,bbox_distance,bbox_from_xyxy
    iou(a;b)
    center_in(inner;outer)
    bbox_distance(a;b)
    bbox_from_xyxy(x0;y0;x1;y1)
  imgl/interact.py:
    e: _build_session_catalog,resolve_imgl_uri,_resolve_click,_resolve_type,_annotate_catalog,_select_window,_export_window_previews,run_interactive_shell,describe_resolution,_print_catalog_banner,_handle_window_phase_prompt,InteractSession
    InteractSession:
    _build_session_catalog(session)
    resolve_imgl_uri(uri;session)
    _resolve_click(qs;finder;session)
    _resolve_type(qs;finder;session)
    _annotate_catalog(session)
    _select_window(session;window_ref)
    _export_window_previews(session)
    run_interactive_shell(image_path)
    describe_resolution(resolved)
    _print_catalog_banner(session;cfg;use_llm;no_filter;stderr)
    _handle_window_phase_prompt(prompt)
  imgl/layout.py:
    e: build_windows,find_containing_window,assign_ocr_to_windows,extract_window_titles,_best_titlebar_for_window,_overlaps_top
    build_windows(detected)
    find_containing_window(bbox;windows)
    assign_ocr_to_windows(windows;ocr_boxes)
    extract_window_titles(windows;detected;ocr_boxes)
    _best_titlebar_for_window(window_bbox;titlebars)
    _overlaps_top(window_bbox;bar_bbox)
  imgl/llm_catalog.py:
    e: _env_file_candidates,_load_env_files,llm_available,llm_dependencies_ok,refine_catalog_with_llm,_heuristic_fallback,_short_error,_call_vision_llm,_parse_json_payload,_image_to_base64,_llm_json_to_options,_snap_options_to_scene,_merge_heuristic_inputs,_overlaps_catalog,_renumber_options,_best_label_match
    _env_file_candidates()
    _load_env_files()
    llm_available()
    llm_dependencies_ok()
    refine_catalog_with_llm(scene)
    _heuristic_fallback(scene)
    _short_error(exc)
    _call_vision_llm(image_path)
    _parse_json_payload(content)
    _image_to_base64(image_path)
    _llm_json_to_options(payload)
    _snap_options_to_scene(options;scene)
    _merge_heuristic_inputs(llm_options;scene)
    _overlaps_catalog(option;others)
    _renumber_options(options)
    _best_label_match(label;candidates)
  imgl/nlp2uri.py:
    e: prompt_to_imgl_uri,_delegate_vql_nlp2uri,_find_catalog_by_text,_find_catalog_input,_match_catalog_action,ResolvedImglUri
    ResolvedImglUri: to_dict(0)
    prompt_to_imgl_uri(prompt)
    _delegate_vql_nlp2uri(prompt)
    _find_catalog_by_text(catalog;query)
    _find_catalog_input(catalog;hint)
    _match_catalog_action(catalog;hint)
  imgl/ocr/__init__.py:
    e: get_ocr_backend
    get_ocr_backend(name)
  imgl/ocr/base.py:
    e: OcrBackend
    OcrBackend: run(1)
  imgl/ocr/lang.py:
    e: normalize_ocr_lang,ocr_lang_attempts
    normalize_ocr_lang(lang)
    ocr_lang_attempts(lang)
  imgl/ocr/tesseract.py:
    e: _level_name,TesseractOcr
    TesseractOcr: run(1)  # Extract word-level bounding boxes using pytesseract.
    _level_name(level)
  imgl/paths.py:
    e: resolve_image_path,resolve_image_path_optional
    resolve_image_path(source)
    resolve_image_path_optional(source)
  imgl/pipeline.py:
    e: analyze,_content_metadata,_count_roles
    analyze(image)
    _content_metadata(diag)
    _count_roles(windows;orphan_elements)
  imgl/preprocess.py:
    e: load_image,preprocess,PreprocessedImage
    PreprocessedImage:
    load_image(source)
    preprocess(source)
  imgl/scene_cache.py:
    e: scene_cache_path,load_cached_scene,save_scene_cache,load_or_analyze
    scene_cache_path(vql_file)
    load_cached_scene(image_path;vql_file)
    save_scene_cache(scene;vql_file)
    load_or_analyze(image_path)
  imgl/types.py:
    e: dataclass_to_dict,BBox,OcrBox,Element,Window,Scene
    BBox: as_xyxy(0),contains(1),to_dict(0),from_xyxy(5)
    OcrBox: to_dict(0)
    Element: to_dict(0)
    Window: to_dict(0)
    Scene: to_dict(0),from_dict(2)
    dataclass_to_dict(obj)
  imgl/uri.py:
    e: _imgl_uri,uri_for_imgl_analyze,uri_for_imgl_annotate,uri_for_imgl_list,uri_for_imgl_click,uri_for_imgl_type,uri_for_imgl_action
    _imgl_uri()
    uri_for_imgl_analyze()
    uri_for_imgl_annotate()
    uri_for_imgl_list()
    uri_for_imgl_click()
    uri_for_imgl_type()
    uri_for_imgl_action()
  imgl/vdisplay_bridge.py:
    e: vdisplay_available,vdisplay_missing_message,default_display,list_os_windows,list_os_monitors,diagnose_os_display,_norm,find_os_window,suggest_imgl_region,list_vision_windows,correlate_windows,build_window_control_report
    vdisplay_available()
    vdisplay_missing_message()
    default_display()
    list_os_windows()
    list_os_monitors()
    diagnose_os_display()
    _norm(value)
    find_os_window(match)
    suggest_imgl_region(window)
    list_vision_windows(image)
    correlate_windows(os_windows;vision_windows)
    build_window_control_report(image)
  imgl/web/__init__.py:
    e: create_app
    create_app()
  imgl/web/agent.py:
    e: _catalog_lines,_history_lines,pick_agent_action,_parse_agent_json
    _catalog_lines(catalog)
    _history_lines(history;limit)
    pick_agent_action(goal;catalog;history)
    _parse_agent_json(raw)
  imgl/web/app.py:
    e: create_app,SettingsBody,WindowBody,ActBody,CaptureBody,AgentStartBody,AgentStepBody
    SettingsBody:
    WindowBody:
    ActBody:
    CaptureBody:
    AgentStartBody:
    AgentStepBody:
    create_app()
  imgl/web/session.py:
    e: StepRecord,AgentState,WebSettings,WebSession,SessionManager
    StepRecord: to_dict(0)
    AgentState: to_dict(0)
    WebSettings: to_dict(0)
    WebSession: __post_init__(0),refresh_catalog(0),analyze(0),capture(0),select_window(1),resolve_prompt(1),resolve_index(1),act(0),state_dict(0),_refresh_annotated_png(0),_interact_session(0),_step_record(0)
    SessionManager: __init__(1),create(1),auto_select_first_window(0)  # Single global session for local desktop control.
  imgl/web/thumbs.py:
    e: _clamp_box,crop_bbox_png,window_bbox_dict
    _clamp_box(bbox)
    crop_bbox_png(image_path;bbox)
    window_bbox_dict(window)
  imgl/window_scope.py:
    e: is_monolithic_scene,apply_discovered_windows,discover_windows,summarize_windows,format_window_picker,get_discovered_window,scene_for_window,crop_window_image,export_window_crop,default_window_annotated_path,_split_monolithic_window,_collect_elements,_detect_layout_mode,_split_side_by_side,_split_stacked,_image_gutter_candidates,_element_gap_gutters,_regions_from_balanced_gutters,_split_by_element_y_gaps,_best_vertical_split,_region_id_for_boxes,_guess_window_title,_shift_elements,_shift_ocr_boxes,_safe_filename,WindowSummary
    WindowSummary: label(0),bbox(0)  # One discoverable window region with stats for the picker UI.
    is_monolithic_scene(scene)
    apply_discovered_windows(scene)
    discover_windows(scene)
    summarize_windows(scene)
    format_window_picker(summaries)
    get_discovered_window(scene;window_ref)
    scene_for_window(scene;window)
    crop_window_image(image_path;window)
    export_window_crop(image_path;window)
    default_window_annotated_path(image_path;window_id)
    _split_monolithic_window(scene)
    _collect_elements(scene)
    _detect_layout_mode(elements;window_bbox)
    _split_side_by_side(window_bbox;elements)
    _split_stacked(window_bbox;elements)
    _image_gutter_candidates(image_path;window_bbox)
    _element_gap_gutters(window_bbox;elements)
    _regions_from_balanced_gutters(window_bbox;elements;candidates)
    _split_by_element_y_gaps(window_bbox;elements)
    _best_vertical_split(elements;window_bbox)
    _region_id_for_boxes(index;count;layout)
    _guess_window_title(window;ocr_boxes)
    _shift_elements(elements;origin)
    _shift_ocr_boxes(boxes;origin)
    _safe_filename(value)
  packages/cli2imgl/src/cli2imgl/cli.py:
    e: main
    main(argv)
  packages/dsl2imgl/src/dsl2imgl/__init__.py:
  packages/dsl2imgl/src/dsl2imgl/bus.py:
    e: _run_handler,dispatch,execute_dsl_line,execute_dsl,dispatch_json
    _run_handler(payload)
    dispatch(envelope)
    execute_dsl_line(line)
    execute_dsl(text)
    dispatch_json(data)
  packages/dsl2imgl/src/dsl2imgl/cli.py:
    e: main
    main(argv)
  packages/dsl2imgl/src/dsl2imgl/codec.py:
    e: validate_payload,parse_text,envelope_to_bytes,envelope_from_bytes,envelope_to_json,envelope_from_json,roundtrip_text
    validate_payload(payload)
    parse_text(line)
    envelope_to_bytes(payload)
    envelope_from_bytes(data)
    envelope_to_json(payload)
    envelope_from_json(data)
    roundtrip_text(line)
  packages/dsl2imgl/src/dsl2imgl/engine.py:
  packages/dsl2imgl/src/dsl2imgl/events.py:
    e: StoredEvent,EventStore
    StoredEvent: to_dict(0)
    EventStore: __init__(1),for_default(2),append_command(2),_append_pb(1),_append_jsonl(1),replay_pb(0),replay(0)
  packages/dsl2imgl/src/dsl2imgl/grammar.py:
    e: split_command,pick_flag,parse_line,to_text
    split_command(line)
    pick_flag(tokens;flag)
    parse_line(line)
    to_text(cmd)
  packages/dsl2imgl/src/dsl2imgl/handlers/__init__.py:
  packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py:
    e: _build_interact_session,_run_prompt_act,handle_health,handle_capture,handle_analyze,handle_actions,handle_resolve,handle_execute
    _build_interact_session()
    _run_prompt_act(session)
    handle_health(_cmd)
    handle_capture(cmd)
    handle_analyze(cmd)
    handle_actions(cmd)
    handle_resolve(cmd)
    handle_execute(cmd)
  packages/dsl2imgl/src/dsl2imgl/pb_codec.py:
    e: _set_body,dict_to_envelope,envelope_to_dict,encode_protobuf,decode_protobuf,encode_text_to_protobuf,decode_protobuf_to_text,result_to_pb,pb_to_result,encode_result_protobuf
    _set_body(envelope;cmd)
    dict_to_envelope(cmd)
    envelope_to_dict(envelope)
    encode_protobuf(cmd)
    decode_protobuf(data)
    encode_text_to_protobuf(line)
    decode_protobuf_to_text(data)
    result_to_pb(result)
    pb_to_result(pb)
    encode_result_protobuf(result)
  packages/dsl2imgl/src/dsl2imgl/result.py:
    e: DslResult
    DslResult: to_dict(0),to_json(0)
  packages/dsl2imgl/src/dsl2imgl/schema_registry.py:
    e: _load_schemas,schema_for_verb,all_verbs,validate_schemas
    _load_schemas()
    schema_for_verb(verb)
    all_verbs()
    validate_schemas()
  packages/dsl2imgl/src/dsl2imgl/v1/__init__.py:
  packages/dsl2imgl/src/dsl2imgl/v1/command_pb2.py:
  packages/dsl2imgl/src/dsl2imgl/v1/result_pb2.py:
  packages/dsl2imgl/tests/test_dsl2imgl.py:
    e: test_health,test_grammar_roundtrip,test_key_dry_run,test_key_parses_trailing_image_window
    test_health()
    test_grammar_roundtrip()
    test_key_dry_run()
    test_key_parses_trailing_image_window()
  packages/dsl2imgl/tests/test_dsl2imgl_phase4.py:
    e: test_schema_registry_covers_all_verbs,test_parse_text_validates_health,test_protobuf_roundtrip_type,test_codec_roundtrip_text,test_dispatch_bytes_envelope,test_event_store_append_command,test_command_dispatch_records_event_id
    test_schema_registry_covers_all_verbs()
    test_parse_text_validates_health()
    test_protobuf_roundtrip_type()
    test_codec_roundtrip_text()
    test_dispatch_bytes_envelope()
    test_event_store_append_command(tmp_path)
    test_command_dispatch_records_event_id(tmp_path;monkeypatch)
  packages/mcp2imgl/src/mcp2imgl/cli.py:
    e: main
    main(argv)
  packages/mcp2imgl/src/mcp2imgl/server.py:
    e: run_stdio
    run_stdio()
  packages/nlp2imgl/src/nlp2imgl/__init__.py:
  packages/nlp2imgl/src/nlp2imgl/cli.py:
    e: main
    main(argv)
  packages/nlp2imgl/src/nlp2imgl/control.py:
    e: default_image_path,default_window,_result_to_dict,doctor_capture,apply_nl_with_diag
    default_image_path()
    default_window()
    _result_to_dict(result)
    doctor_capture(image)
    apply_nl_with_diag(prompt)
  packages/nlp2imgl/src/nlp2imgl/to_dsl.py:
    e: use_llm_enabled,to_dsl,apply_nl
    use_llm_enabled(explicit)
    to_dsl(prompt)
    apply_nl(prompt)
  packages/rest2imgl/src/rest2imgl/app.py:
    e: create_app,NlBody,DoctorBody
    NlBody:
    DoctorBody:
    create_app()
  packages/rest2imgl/src/rest2imgl/cli.py:
    e: main
    main(argv)
  packages/uri2imgl/src/uri2imgl/__init__.py:
  packages/uri2imgl/src/uri2imgl/cli.py:
    e: main
    main(argv)
  packages/uri2imgl/src/uri2imgl/decode.py:
    e: uri_to_dsl
    uri_to_dsl(uri)
  tests/test_actions.py:
    e: _dialog_scene,test_find_button_by_text,test_find_input_by_label,test_click_coords,test_click_action,test_type_into_by_label,test_find_in_window,test_find_one_not_found,test_click_raises_when_missing,test_list_actions,test_cli_find_command
    _dialog_scene()
    test_find_button_by_text()
    test_find_input_by_label()
    test_click_coords()
    test_click_action()
    test_type_into_by_label()
    test_find_in_window()
    test_find_one_not_found()
    test_click_raises_when_missing()
    test_list_actions()
    test_cli_find_command(tmp_path;capsys)
  tests/test_annotate.py:
    e: _scene,test_default_annotated_path,test_write_annotated_image,test_nlp2uri_mapa
    _scene()
    test_default_annotated_path()
    test_write_annotated_image(tmp_path)
    test_nlp2uri_mapa()
  tests/test_autodiag.py:
    e: test_image_freshness_sidecar,test_verify_capture_updated_fails_on_stale,test_build_execute_report_json,test_diagnose_capture_stale,test_is_valid_png_rejects_empty,test_vql_cache_path_names
    test_image_freshness_sidecar(tmp_path)
    test_verify_capture_updated_fails_on_stale(tmp_path)
    test_build_execute_report_json()
    test_diagnose_capture_stale(tmp_path;monkeypatch)
    test_is_valid_png_rejects_empty(tmp_path)
    test_vql_cache_path_names()
  tests/test_capture_paths.py:
    e: test_resolve_image_path_absolute,test_resolve_image_path_relative,test_resolve_image_path_not_found,test_resolve_image_path_optional,test_cli_missing_image_friendly_error,test_capture_default_path,test_cli_vql_aborts_on_blank,test_cli_vql_allows_blank_with_flag,test_capture_screen_with_mock_vql
    test_resolve_image_path_absolute(tmp_path)
    test_resolve_image_path_relative(tmp_path;monkeypatch)
    test_resolve_image_path_not_found(tmp_path;monkeypatch)
    test_resolve_image_path_optional()
    test_cli_missing_image_friendly_error(tmp_path;capsys)
    test_capture_default_path(tmp_path)
    test_cli_vql_aborts_on_blank(tmp_path)
    test_cli_vql_allows_blank_with_flag(tmp_path)
    test_capture_screen_with_mock_vql(tmp_path)
  tests/test_catalog_filter.py:
    e: _noisy_scene,test_filter_catalog_drops_code_and_generic,test_build_interactive_catalog_filtered_by_default
    _noisy_scene()
    test_filter_catalog_drops_code_and_generic()
    test_build_interactive_catalog_filtered_by_default()
  tests/test_catalog_interact.py:
    e: _dialog_scene,test_build_interactive_catalog,test_format_catalog_table_contains_indices,test_prompt_to_imgl_uri_click_polish,test_prompt_to_imgl_uri_type_polish,test_prompt_to_imgl_uri_number,test_resolve_imgl_uri_click,test_resolve_imgl_uri_list,test_resolve_imgl_uri_type,test_catalog_input_number_is_click,test_interactive_shell_quit
    _dialog_scene()
    test_build_interactive_catalog()
    test_format_catalog_table_contains_indices()
    test_prompt_to_imgl_uri_click_polish()
    test_prompt_to_imgl_uri_type_polish()
    test_prompt_to_imgl_uri_number()
    test_resolve_imgl_uri_click()
    test_resolve_imgl_uri_list()
    test_resolve_imgl_uri_type()
    test_catalog_input_number_is_click()
    test_interactive_shell_quit(monkeypatch)
  tests/test_diagnose.py:
    e: _black_image,_ui_like_image,test_worth_analyzing_blank_scene,test_worth_analyzing_ui_scene,test_diagnose_black_image_fallback,test_diagnose_with_img2nl_black,test_diagnose_with_img2nl_ui,test_pipeline_skip_blank_raises,test_pipeline_includes_content_metadata,test_cli_diagnose_command
    _black_image(path;size)
    _ui_like_image(path)
    test_worth_analyzing_blank_scene()
    test_worth_analyzing_ui_scene()
    test_diagnose_black_image_fallback(tmp_path)
    test_diagnose_with_img2nl_black(tmp_path)
    test_diagnose_with_img2nl_ui(tmp_path)
    test_pipeline_skip_blank_raises(tmp_path)
    test_pipeline_includes_content_metadata(tmp_path)
    test_cli_diagnose_command(tmp_path;capsys)
  tests/test_execute_key.py:
    e: test_normalize_keys,test_execute_key_dry_run
    test_normalize_keys()
    test_execute_key_dry_run()
  tests/test_export.py:
    e: _make_dialog_fixture,_sample_scene,test_scene_to_html_structure,test_scene_to_html_embed_image,test_scene_to_html_escapes_special_chars,test_scene_to_svg_wireframe,test_scene_to_svg_overlay,test_scene_to_svg_invalid_mode,test_cli_html_command,test_cli_svg_command_writes_file,test_cli_svg_wireframe_default
    _make_dialog_fixture(path)
    _sample_scene()
    test_scene_to_html_structure()
    test_scene_to_html_embed_image()
    test_scene_to_html_escapes_special_chars()
    test_scene_to_svg_wireframe()
    test_scene_to_svg_overlay()
    test_scene_to_svg_invalid_mode()
    test_cli_html_command(tmp_path;capsys)
    test_cli_svg_command_writes_file(tmp_path)
    test_cli_svg_wireframe_default(tmp_path;capsys)
  tests/test_imgl.py:
    e: _make_text_image,test_import,test_bbox_as_xyxy_and_contains,test_scene_roundtrip_json,test_scene_from_dict,test_preprocess_resize,test_analyze_with_mocked_ocr,test_analyze_e2e_with_tesseract,test_cli_analyze_stdout,test_cli_analyze_output_file
    _make_text_image(path;text)
    test_import()
    test_bbox_as_xyxy_and_contains()
    test_scene_roundtrip_json()
    test_scene_from_dict()
    test_preprocess_resize()
    test_analyze_with_mocked_ocr(tmp_path)
    test_analyze_e2e_with_tesseract(tmp_path)
    test_cli_analyze_stdout(tmp_path;capsys)
    test_cli_analyze_output_file(tmp_path)
  tests/test_layout_classify.py:
    e: _font,_make_dialog_fixture,test_iou_and_center_in,test_build_windows_fallback,test_build_windows_from_panels,test_find_containing_window,test_extract_window_titles,test_classify_button_with_geometry,test_classify_label_input_pair,test_detect_ui_elements_on_fixture,test_analyze_classifies_dialog
    _font(size)
    _make_dialog_fixture(path)
    test_iou_and_center_in()
    test_build_windows_fallback()
    test_build_windows_from_panels()
    test_find_containing_window()
    test_extract_window_titles()
    test_classify_button_with_geometry()
    test_classify_label_input_pair()
    test_detect_ui_elements_on_fixture(tmp_path)
    test_analyze_classifies_dialog(tmp_path)
  tests/test_llm_catalog.py:
    e: test_load_env_files_reads_dotenv,test_snap_options_to_scene,test_merge_heuristic_inputs_appends_missing_fields
    test_load_env_files_reads_dotenv(tmp_path;monkeypatch)
    test_snap_options_to_scene()
    test_merge_heuristic_inputs_appends_missing_fields()
  tests/test_nlp2imgl_control.py:
    e: test_apply_nl_with_diag_blocks_stale
    test_apply_nl_with_diag_blocks_stale(monkeypatch)
  tests/test_nlp2imgl_llm.py:
    e: test_to_dsl_adds_llm_flag,test_to_dsl_explicit_llm_false,test_use_llm_from_openrouter_key
    test_to_dsl_adds_llm_flag(monkeypatch)
    test_to_dsl_explicit_llm_false(monkeypatch)
    test_use_llm_from_openrouter_key(monkeypatch)
  tests/test_nlp2uri_fixes.py:
    e: _scene_with_search_input,test_click_before_type_for_type_to_search_label,test_type_into_search_field_from_catalog
    _scene_with_search_input()
    test_click_before_type_for_type_to_search_label()
    test_type_into_search_field_from_catalog()
  tests/test_ocr_lang.py:
    e: test_normalize_url_decoded_lang,test_ocr_lang_attempts_fallback
    test_normalize_url_decoded_lang()
    test_ocr_lang_attempts_fallback()
  tests/test_scene_cache.py:
    e: test_scale_scene_to_screen_doubles_coords,test_scene_cache_roundtrip,test_load_or_analyze_uses_cache
    test_scale_scene_to_screen_doubles_coords()
    test_scene_cache_roundtrip(tmp_path)
    test_load_or_analyze_uses_cache(tmp_path;monkeypatch)
  tests/test_vdisplay_bridge.py:
    e: test_suggest_imgl_region_bottom,test_suggest_imgl_region_top,test_correlate_windows_finds_overlap,test_vdisplay_available_is_bool
    test_suggest_imgl_region_bottom()
    test_suggest_imgl_region_top()
    test_correlate_windows_finds_overlap()
    test_vdisplay_available_is_bool()
  tests/test_vql_export.py:
    e: _sample_scene,test_scene_to_vql_structure,test_scene_to_vql_json_roundtrip,test_write_vql_program,test_cli_vql_command
    _sample_scene()
    test_scene_to_vql_structure()
    test_scene_to_vql_json_roundtrip()
    test_write_vql_program(tmp_path)
    test_cli_vql_command(tmp_path;capsys)
  tests/test_web.py:
    e: _write_ui_fixture,web_client,test_health,test_index_html,test_state_and_screenshot,test_act_dry_run_by_index,test_action_thumb,test_settings_update,test_capture_error_returns_state,test_agent_start_without_llm
    _write_ui_fixture(path)
    web_client(tmp_path)
    test_health(web_client)
    test_index_html(web_client)
    test_state_and_screenshot(web_client)
    test_act_dry_run_by_index(web_client)
    test_action_thumb(web_client)
    test_settings_update(web_client)
    test_capture_error_returns_state(web_client;monkeypatch)
    test_agent_start_without_llm(web_client)
  tests/test_window_scope.py:
    e: _wide_scene,test_discover_windows_splits_monolithic_scene,test_scene_for_window_shifts_coordinates,test_build_catalog_scoped_to_window,test_export_window_crop_and_preview,test_stacked_layout_splits_horizontally_not_grid,test_format_window_picker_lists_regions,test_single_monitor_region_bottom_alias
    _wide_scene()
    test_discover_windows_splits_monolithic_scene()
    test_scene_for_window_shifts_coordinates()
    test_build_catalog_scoped_to_window()
    test_export_window_crop_and_preview(tmp_path)
    test_stacked_layout_splits_horizontally_not_grid(tmp_path)
    test_format_window_picker_lists_regions()
    test_single_monitor_region_bottom_alias()
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('imgl', '0.7.2', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 212, 'less').
project_file('examples/scripts/demo-agent-loop.sh', 38, 'shell').
project_file('examples/scripts/demo-github.sh', 22, 'shell').
project_file('examples/scripts/demo-nlp2uri.py', 80, 'python').
project_file('examples/scripts/demo-windows.sh', 23, 'shell').
project_file('imgl/__init__.py', 52, 'python').
project_file('imgl/__main__.py', 7, 'python').
project_file('imgl/actions.py', 272, 'python').
project_file('imgl/autodiag.py', 407, 'python').
project_file('imgl/capture.py', 212, 'python').
project_file('imgl/catalog.py', 351, 'python').
project_file('imgl/catalog_filter.py', 139, 'python').
project_file('imgl/classify/__init__.py', 6, 'python').
project_file('imgl/classify/gui_heuristics.py', 262, 'python').
project_file('imgl/cli.py', 718, 'python').
project_file('imgl/config.py', 24, 'python').
project_file('imgl/coords.py', 71, 'python').
project_file('imgl/detect/__init__.py', 12, 'python').
project_file('imgl/detect/img2vql_bridge.py', 65, 'python').
project_file('imgl/detect/local.py', 279, 'python').
project_file('imgl/detect/rectangles.py', 97, 'python').
project_file('imgl/diagnose.py', 248, 'python').
project_file('imgl/execute.py', 163, 'python').
project_file('imgl/export/__init__.py', 31, 'python').
project_file('imgl/export/_escape.py', 20, 'python').
project_file('imgl/export/annotate_export.py', 300, 'python').
project_file('imgl/export/html_export.py', 150, 'python').
project_file('imgl/export/json_export.py', 23, 'python').
project_file('imgl/export/svg_export.py', 138, 'python').
project_file('imgl/export/vql_adapter.py', 245, 'python').
project_file('imgl/freshness.py', 152, 'python').
project_file('imgl/geometry.py', 38, 'python').
project_file('imgl/interact.py', 561, 'python').
project_file('imgl/layout.py', 109, 'python').
project_file('imgl/llm_catalog.py', 521, 'python').
project_file('imgl/nlp2uri.py', 283, 'python').
project_file('imgl/ocr/__init__.py', 13, 'python').
project_file('imgl/ocr/base.py', 15, 'python').
project_file('imgl/ocr/lang.py', 33, 'python').
project_file('imgl/ocr/tesseract.py', 95, 'python').
project_file('imgl/paths.py', 42, 'python').
project_file('imgl/pipeline.py', 117, 'python').
project_file('imgl/preprocess.py', 64, 'python').
project_file('imgl/scene_cache.py', 64, 'python').
project_file('imgl/types.py', 171, 'python').
project_file('imgl/uri.py', 119, 'python').
project_file('imgl/vdisplay_bridge.py', 254, 'python').
project_file('imgl/web/__init__.py', 11, 'python').
project_file('imgl/web/agent.py', 153, 'python').
project_file('imgl/web/app.py', 287, 'python').
project_file('imgl/web/session.py', 453, 'python').
project_file('imgl/web/thumbs.py', 56, 'python').
project_file('imgl/window_scope.py', 576, 'python').
project_file('packages/cli2imgl/src/cli2imgl/cli.py', 35, 'python').
project_file('packages/dsl2imgl/scripts/generate-proto.sh', 7, 'shell').
project_file('packages/dsl2imgl/src/dsl2imgl/__init__.py', 7, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/bus.py', 111, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/cli.py', 47, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/codec.py', 58, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/engine.py', 6, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/events.py', 169, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/grammar.py', 138, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/handlers/__init__.py', 2, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 221, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 241, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/result.py', 35, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/schema_registry.py', 45, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/v1/__init__.py', 2, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/v1/command_pb2.py', 57, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/v1/result_pb2.py', 40, 'python').
project_file('packages/dsl2imgl/tests/test_dsl2imgl.py', 38, 'python').
project_file('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 71, 'python').
project_file('packages/mcp2imgl/src/mcp2imgl/cli.py', 23, 'python').
project_file('packages/mcp2imgl/src/mcp2imgl/server.py', 36, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/__init__.py', 5, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/cli.py', 92, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/control.py', 151, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 94, 'python').
project_file('packages/rest2imgl/src/rest2imgl/app.py', 126, 'python').
project_file('packages/rest2imgl/src/rest2imgl/cli.py', 27, 'python').
project_file('packages/uri2imgl/src/uri2imgl/__init__.py', 4, 'python').
project_file('packages/uri2imgl/src/uri2imgl/cli.py', 37, 'python').
project_file('packages/uri2imgl/src/uri2imgl/decode.py', 36, 'python').
project_file('project.sh', 59, 'shell').
project_file('tests/test_actions.py', 140, 'python').
project_file('tests/test_annotate.py', 59, 'python').
project_file('tests/test_autodiag.py', 91, 'python').
project_file('tests/test_capture_paths.py', 105, 'python').
project_file('tests/test_catalog_filter.py', 73, 'python').
project_file('tests/test_catalog_interact.py', 200, 'python').
project_file('tests/test_diagnose.py', 147, 'python').
project_file('tests/test_execute_key.py', 17, 'python').
project_file('tests/test_export.py', 218, 'python').
project_file('tests/test_imgl.py', 202, 'python').
project_file('tests/test_layout_classify.py', 176, 'python').
project_file('tests/test_llm_catalog.py', 127, 'python').
project_file('tests/test_nlp2imgl_control.py', 36, 'python').
project_file('tests/test_nlp2imgl_llm.py', 29, 'python').
project_file('tests/test_nlp2uri_fixes.py', 63, 'python').
project_file('tests/test_ocr_lang.py', 17, 'python').
project_file('tests/test_scene_cache.py', 90, 'python').
project_file('tests/test_vdisplay_bridge.py', 51, 'python').
project_file('tests/test_vql_export.py', 106, 'python').
project_file('tests/test_web.py', 121, 'python').
project_file('tests/test_window_scope.py', 198, 'python').
project_file('tree.sh', 2, 'shell').

% ── Python Functions ─────────────────────────────────────
python_function('examples/scripts/demo-nlp2uri.py', 'main', 0, 7, 13).
python_function('imgl/actions.py', 'actions', 1, 1, 1).
python_function('imgl/actions.py', '_format_query', 1, 5, 2).
python_function('imgl/actions.py', '_text_matches', 2, 3, 1).
python_function('imgl/actions.py', '_iter_elements', 1, 9, 2).
python_function('imgl/actions.py', '_window_matches', 2, 4, 1).
python_function('imgl/actions.py', '_find_label_for_input', 3, 6, 5).
python_function('imgl/autodiag.py', 'img2nl_root', 0, 1, 4).
python_function('imgl/autodiag.py', 'img2nl_available', 0, 1, 2).
python_function('imgl/autodiag.py', 'diagnose_capture', 1, 16, 16).
python_function('imgl/autodiag.py', 'build_operation_step', 1, 19, 9).
python_function('imgl/autodiag.py', '_compact_result', 1, 6, 3).
python_function('imgl/autodiag.py', 'build_execute_report', 0, 5, 5).
python_function('imgl/autodiag.py', 'pick_output_format', 2, 7, 2).
python_function('imgl/autodiag.py', 'render_report', 2, 3, 4).
python_function('imgl/autodiag.py', '_flag_enabled', 0, 3, 3).
python_function('imgl/autodiag.py', 'should_block_blank_capture', 1, 2, 2).
python_function('imgl/autodiag.py', 'should_block_stale_capture', 1, 3, 2).
python_function('imgl/autodiag.py', 'diagnostics_enabled', 0, 1, 1).
python_function('imgl/autodiag.py', '_render_markdown', 1, 24, 7).
python_function('imgl/autodiag.py', '_overall_verdict', 2, 10, 1).
python_function('imgl/autodiag.py', '_actionable_hints', 1, 12, 3).
python_function('imgl/autodiag.py', '_compact_features', 1, 6, 1).
python_function('imgl/autodiag.py', '_scene_class', 1, 2, 2).
python_function('imgl/autodiag.py', '_parse_coords', 1, 2, 3).
python_function('imgl/autodiag.py', '_coords_from_action', 1, 3, 1).
python_function('imgl/autodiag.py', '_parse_typed_text', 1, 2, 2).
python_function('imgl/autodiag.py', '_parse_keys', 1, 2, 3).
python_function('imgl/capture.py', 'default_capture_path', 1, 2, 6).
python_function('imgl/capture.py', '_is_wayland', 0, 3, 3).
python_function('imgl/capture.py', 'capture_screen', 1, 13, 10).
python_function('imgl/capture.py', '_try_vql_capture', 1, 8, 7).
python_function('imgl/capture.py', '_native_backends', 0, 3, 4).
python_function('imgl/capture.py', '_run_command', 2, 3, 4).
python_function('imgl/capture.py', '_capture_with_grim', 1, 2, 3).
python_function('imgl/capture.py', '_capture_with_gnome_screenshot', 1, 2, 3).
python_function('imgl/capture.py', '_capture_with_scrot', 1, 2, 3).
python_function('imgl/capture.py', '_capture_with_portal', 1, 3, 5).
python_function('imgl/capture.py', '_capture_with_mss', 1, 1, 8).
python_function('imgl/capture.py', '_is_blank_image', 1, 6, 13).
python_function('imgl/capture.py', 'capture_status_message', 1, 2, 1).
python_function('imgl/catalog.py', 'build_interactive_catalog', 1, 12, 10).
python_function('imgl/catalog.py', 'format_catalog_table', 1, 8, 4).
python_function('imgl/catalog.py', '_window_option', 2, 2, 4).
python_function('imgl/catalog.py', '_element_option', 2, 13, 9).
python_function('imgl/catalog.py', '_infer_input_label', 2, 13, 0).
python_function('imgl/catalog.py', '_find_window', 2, 2, 1).
python_function('imgl/catalog.py', '_iter_interactive_elements', 1, 9, 1).
python_function('imgl/catalog.py', '_truncate', 2, 2, 3).
python_function('imgl/catalog_filter.py', 'filter_catalog', 1, 8, 6).
python_function('imgl/catalog_filter.py', '_renumber', 1, 2, 4).
python_function('imgl/catalog_filter.py', '_replace_index_in_uri', 2, 1, 0).
python_function('imgl/catalog_filter.py', '_keep_element', 1, 17, 8).
python_function('imgl/catalog_filter.py', '_element_score', 1, 9, 4).
python_function('imgl/catalog_filter.py', '_window_score', 1, 5, 1).
python_function('imgl/classify/gui_heuristics.py', 'classify_scene_elements', 4, 27, 15).
python_function('imgl/classify/gui_heuristics.py', '_normalize_confidence', 1, 2, 0).
python_function('imgl/classify/gui_heuristics.py', '_word_count', 1, 1, 2).
python_function('imgl/classify/gui_heuristics.py', '_text_or_label', 1, 7, 4).
python_function('imgl/classify/gui_heuristics.py', '_label_candidates', 2, 5, 3).
python_function('imgl/classify/gui_heuristics.py', '_match_ocr_to_bbox', 3, 5, 3).
python_function('imgl/classify/gui_heuristics.py', '_nearest_label', 3, 7, 3).
python_function('imgl/classify/gui_heuristics.py', '_ocr_inside_frame', 3, 4, 1).
python_function('imgl/classify/gui_heuristics.py', '_build_inputs', 0, 7, 7).
python_function('imgl/cli.py', '_add_common_args', 1, 1, 1).
python_function('imgl/cli.py', 'build_parser', 0, 1, 6).
python_function('imgl/cli.py', '_write_output', 2, 2, 2).
python_function('imgl/cli.py', 'main', 1, 44, 41).
python_function('imgl/cli.py', '_check_blank_before_analyze', 1, 5, 4).
python_function('imgl/cli.py', '_apply_config_overrides', 2, 2, 1).
python_function('imgl/cli.py', '_run_image_command', 3, 19, 28).
python_function('imgl/coords.py', 'scale_scene_to_screen', 1, 6, 11).
python_function('imgl/detect/img2vql_bridge.py', 'img2vql_available', 0, 2, 0).
python_function('imgl/detect/img2vql_bridge.py', '_from_img2vql_dict', 1, 1, 5).
python_function('imgl/detect/img2vql_bridge.py', 'detect_with_img2vql', 1, 4, 4).
python_function('imgl/detect/img2vql_bridge.py', 'detect_ui_merged', 1, 4, 2).
python_function('imgl/detect/local.py', '_hex_color', 1, 1, 0).
python_function('imgl/detect/local.py', '_avg_color', 5, 5, 6).
python_function('imgl/detect/local.py', '_iou_xyxy', 2, 3, 2).
python_function('imgl/detect/local.py', '_detect_titlebar', 3, 5, 10).
python_function('imgl/detect/local.py', '_flood_rects', 1, 14, 7).
python_function('imgl/detect/local.py', '_detect_buttons', 3, 24, 24).
python_function('imgl/detect/local.py', '_detect_panels_simple', 3, 23, 14).
python_function('imgl/detect/local.py', '_dedupe', 1, 8, 5).
python_function('imgl/detect/local.py', 'detect_ui_elements', 1, 4, 6).
python_function('imgl/detect/rectangles.py', 'detect_input_frames', 1, 14, 15).
python_function('imgl/detect/rectangles.py', '_find_rectangular_frames', 1, 11, 6).
python_function('imgl/detect/rectangles.py', '_looks_like_frame', 5, 6, 2).
python_function('imgl/detect/rectangles.py', '_column_has_edge', 4, 2, 3).
python_function('imgl/detect/rectangles.py', '_row_has_edge', 4, 2, 3).
python_function('imgl/diagnose.py', 'img2nl_available', 0, 2, 0).
python_function('imgl/diagnose.py', 'diagnose_content', 1, 3, 7).
python_function('imgl/diagnose.py', 'worth_analyzing', 1, 6, 3).
python_function('imgl/diagnose.py', 'content_summary', 1, 6, 3).
python_function('imgl/diagnose.py', '_diagnose_with_img2nl', 1, 2, 5).
python_function('imgl/diagnose.py', '_diagnose_fallback', 1, 8, 6).
python_function('imgl/diagnose.py', '_diagnose_pil_fallback', 1, 7, 10).
python_function('imgl/diagnose.py', '_scene_class', 1, 2, 2).
python_function('imgl/diagnose.py', '_has_ui_signals', 1, 7, 2).
python_function('imgl/diagnose.py', '_recommendation', 1, 10, 3).
python_function('imgl/execute.py', 'execute_action', 1, 9, 8).
python_function('imgl/execute.py', '_execute_xdotool', 4, 5, 4).
python_function('imgl/execute.py', '_execute_ydotool', 4, 5, 3).
python_function('imgl/execute.py', 'execute_keys', 1, 5, 5).
python_function('imgl/execute.py', '_normalize_keys', 1, 9, 8).
python_function('imgl/export/_escape.py', 'escape_html', 1, 1, 1).
python_function('imgl/export/_escape.py', 'escape_xml', 1, 1, 1).
python_function('imgl/export/annotate_export.py', 'default_annotated_path', 1, 3, 3).
python_function('imgl/export/annotate_export.py', 'scene_to_annotated_image', 2, 8, 19).
python_function('imgl/export/annotate_export.py', 'write_annotated_image', 3, 1, 5).
python_function('imgl/export/annotate_export.py', 'write_window_preview_images', 3, 3, 19).
python_function('imgl/export/annotate_export.py', 'write_annotated_images_per_window', 2, 5, 4).
python_function('imgl/export/annotate_export.py', 'open_image', 1, 4, 5).
python_function('imgl/export/annotate_export.py', '_catalog_relative_to_window', 2, 2, 2).
python_function('imgl/export/annotate_export.py', '_short_hint_text', 2, 2, 3).
python_function('imgl/export/annotate_export.py', '_short_hint', 2, 4, 3).
python_function('imgl/export/annotate_export.py', '_badge_size', 1, 1, 3).
python_function('imgl/export/annotate_export.py', '_load_fonts', 1, 2, 5).
python_function('imgl/export/annotate_export.py', '_draw_number_badge', 4, 1, 3).
python_function('imgl/export/annotate_export.py', '_text_size', 3, 2, 3).
python_function('imgl/export/annotate_export.py', '_hex_rgba', 2, 1, 2).
python_function('imgl/export/html_export.py', 'scene_to_html', 1, 4, 8).
python_function('imgl/export/html_export.py', '_default_title', 1, 4, 1).
python_function('imgl/export/html_export.py', '_background_layer', 1, 3, 1).
python_function('imgl/export/html_export.py', '_base_css', 0, 1, 0).
python_function('imgl/export/html_export.py', '_render_window', 1, 3, 4).
python_function('imgl/export/html_export.py', '_render_element', 1, 8, 5).
python_function('imgl/export/html_export.py', '_bbox_style', 1, 1, 0).
python_function('imgl/export/json_export.py', 'scene_to_json', 1, 1, 2).
python_function('imgl/export/json_export.py', 'scene_from_json', 1, 2, 3).
python_function('imgl/export/svg_export.py', 'scene_to_svg', 1, 4, 8).
python_function('imgl/export/svg_export.py', '_default_title', 1, 4, 1).
python_function('imgl/export/svg_export.py', '_background_rect', 1, 4, 1).
python_function('imgl/export/svg_export.py', '_svg_css', 0, 1, 0).
python_function('imgl/export/svg_export.py', '_render_window_svg', 1, 3, 4).
python_function('imgl/export/svg_export.py', '_render_element_svg', 1, 4, 4).
python_function('imgl/export/svg_export.py', '_element_css_class', 1, 1, 1).
python_function('imgl/export/vql_adapter.py', 'scene_to_vql', 1, 16, 14).
python_function('imgl/export/vql_adapter.py', 'scene_to_vql_json', 1, 1, 2).
python_function('imgl/export/vql_adapter.py', 'write_vql_program', 2, 1, 3).
python_function('imgl/export/vql_adapter.py', '_grid_layer', 1, 4, 2).
python_function('imgl/export/vql_adapter.py', '_bbox_norm', 3, 5, 2).
python_function('imgl/export/vql_adapter.py', '_location_label', 4, 9, 1).
python_function('imgl/export/vql_adapter.py', '_object_from_bbox', 0, 2, 9).
python_function('imgl/export/vql_adapter.py', '_window_to_object', 3, 2, 1).
python_function('imgl/export/vql_adapter.py', '_element_to_object', 3, 4, 2).
python_function('imgl/export/vql_adapter.py', '_ocr_to_object', 3, 2, 2).
python_function('imgl/freshness.py', 'is_valid_png', 1, 3, 6).
python_function('imgl/freshness.py', 'max_image_age_seconds', 0, 4, 4).
python_function('imgl/freshness.py', 'capture_sidecar_path', 1, 1, 1).
python_function('imgl/freshness.py', 'vql_cache_paths', 1, 1, 1).
python_function('imgl/freshness.py', 'clear_vql_cache', 1, 3, 5).
python_function('imgl/freshness.py', 'sync_vql_cache_with_image', 1, 5, 5).
python_function('imgl/freshness.py', 'mark_capture_fresh', 1, 2, 7).
python_function('imgl/freshness.py', 'image_freshness', 1, 5, 16).
python_function('imgl/freshness.py', 'verify_capture_updated', 2, 4, 8).
python_function('imgl/geometry.py', 'iou', 2, 3, 3).
python_function('imgl/geometry.py', 'center_in', 2, 2, 1).
python_function('imgl/geometry.py', 'bbox_distance', 2, 1, 0).
python_function('imgl/geometry.py', 'bbox_from_xyxy', 4, 1, 1).
python_function('imgl/interact.py', '_build_session_catalog', 1, 2, 1).
python_function('imgl/interact.py', 'resolve_imgl_uri', 2, 13, 16).
python_function('imgl/interact.py', '_resolve_click', 3, 17, 4).
python_function('imgl/interact.py', '_resolve_type', 3, 30, 5).
python_function('imgl/interact.py', '_annotate_catalog', 1, 6, 7).
python_function('imgl/interact.py', '_select_window', 2, 6, 6).
python_function('imgl/interact.py', '_export_window_previews', 1, 4, 5).
python_function('imgl/interact.py', 'run_interactive_shell', 1, 43, 32).
python_function('imgl/interact.py', 'describe_resolution', 1, 1, 0).
python_function('imgl/interact.py', '_print_catalog_banner', 5, 8, 4).
python_function('imgl/interact.py', '_handle_window_phase_prompt', 1, 9, 12).
python_function('imgl/layout.py', 'build_windows', 1, 6, 6).
python_function('imgl/layout.py', 'find_containing_window', 2, 4, 2).
python_function('imgl/layout.py', 'assign_ocr_to_windows', 2, 4, 2).
python_function('imgl/layout.py', 'extract_window_titles', 3, 10, 3).
python_function('imgl/layout.py', '_best_titlebar_for_window', 2, 5, 3).
python_function('imgl/layout.py', '_overlaps_top', 2, 2, 1).
python_function('imgl/llm_catalog.py', '_env_file_candidates', 0, 1, 3).
python_function('imgl/llm_catalog.py', '_load_env_files', 0, 12, 9).
python_function('imgl/llm_catalog.py', 'llm_available', 0, 1, 4).
python_function('imgl/llm_catalog.py', 'llm_dependencies_ok', 0, 2, 0).
python_function('imgl/llm_catalog.py', 'refine_catalog_with_llm', 1, 14, 12).
python_function('imgl/llm_catalog.py', '_heuristic_fallback', 1, 2, 2).
python_function('imgl/llm_catalog.py', '_short_error', 1, 3, 3).
python_function('imgl/llm_catalog.py', '_call_vision_llm', 1, 4, 6).
python_function('imgl/llm_catalog.py', '_parse_json_payload', 1, 3, 3).
python_function('imgl/llm_catalog.py', '_image_to_base64', 1, 3, 12).
python_function('imgl/llm_catalog.py', '_llm_json_to_options', 1, 13, 13).
python_function('imgl/llm_catalog.py', '_snap_options_to_scene', 2, 8, 6).
python_function('imgl/llm_catalog.py', '_merge_heuristic_inputs', 2, 4, 5).
python_function('imgl/llm_catalog.py', '_overlaps_catalog', 2, 4, 3).
python_function('imgl/llm_catalog.py', '_renumber_options', 1, 2, 3).
python_function('imgl/llm_catalog.py', '_best_label_match', 2, 13, 5).
python_function('imgl/nlp2uri.py', 'prompt_to_imgl_uri', 1, 28, 15).
python_function('imgl/nlp2uri.py', '_delegate_vql_nlp2uri', 1, 5, 5).
python_function('imgl/nlp2uri.py', '_find_catalog_by_text', 2, 9, 1).
python_function('imgl/nlp2uri.py', '_find_catalog_input', 2, 9, 2).
python_function('imgl/nlp2uri.py', '_match_catalog_action', 2, 8, 2).
python_function('imgl/ocr/__init__.py', 'get_ocr_backend', 1, 2, 2).
python_function('imgl/ocr/lang.py', 'normalize_ocr_lang', 1, 3, 2).
python_function('imgl/ocr/lang.py', 'ocr_lang_attempts', 1, 6, 5).
python_function('imgl/ocr/tesseract.py', '_level_name', 1, 1, 1).
python_function('imgl/paths.py', 'resolve_image_path', 1, 5, 8).
python_function('imgl/paths.py', 'resolve_image_path_optional', 1, 3, 2).
python_function('imgl/pipeline.py', 'analyze', 1, 11, 19).
python_function('imgl/pipeline.py', '_content_metadata', 1, 1, 2).
python_function('imgl/pipeline.py', '_count_roles', 2, 4, 1).
python_function('imgl/preprocess.py', 'load_image', 1, 2, 6).
python_function('imgl/preprocess.py', 'preprocess', 1, 3, 5).
python_function('imgl/scene_cache.py', 'scene_cache_path', 1, 2, 3).
python_function('imgl/scene_cache.py', 'load_cached_scene', 2, 5, 7).
python_function('imgl/scene_cache.py', 'save_scene_cache', 2, 1, 3).
python_function('imgl/scene_cache.py', 'load_or_analyze', 1, 5, 7).
python_function('imgl/types.py', 'dataclass_to_dict', 1, 2, 3).
python_function('imgl/uri.py', '_imgl_uri', 0, 5, 3).
python_function('imgl/uri.py', 'uri_for_imgl_analyze', 0, 2, 1).
python_function('imgl/uri.py', 'uri_for_imgl_annotate', 0, 2, 1).
python_function('imgl/uri.py', 'uri_for_imgl_list', 0, 1, 1).
python_function('imgl/uri.py', 'uri_for_imgl_click', 0, 5, 1).
python_function('imgl/uri.py', 'uri_for_imgl_type', 0, 5, 1).
python_function('imgl/uri.py', 'uri_for_imgl_action', 0, 1, 1).
python_function('imgl/vdisplay_bridge.py', 'vdisplay_available', 0, 1, 0).
python_function('imgl/vdisplay_bridge.py', 'vdisplay_missing_message', 0, 2, 4).
python_function('imgl/vdisplay_bridge.py', 'default_display', 0, 2, 2).
python_function('imgl/vdisplay_bridge.py', 'list_os_windows', 0, 3, 3).
python_function('imgl/vdisplay_bridge.py', 'list_os_monitors', 0, 3, 3).
python_function('imgl/vdisplay_bridge.py', 'diagnose_os_display', 0, 4, 5).
python_function('imgl/vdisplay_bridge.py', '_norm', 1, 1, 2).
python_function('imgl/vdisplay_bridge.py', 'find_os_window', 1, 6, 4).
python_function('imgl/vdisplay_bridge.py', 'suggest_imgl_region', 1, 5, 3).
python_function('imgl/vdisplay_bridge.py', 'list_vision_windows', 1, 4, 10).
python_function('imgl/vdisplay_bridge.py', 'correlate_windows', 2, 18, 7).
python_function('imgl/vdisplay_bridge.py', 'build_window_control_report', 1, 19, 20).
python_function('imgl/web/__init__.py', 'create_app', 0, 1, 1).
python_function('imgl/web/agent.py', '_catalog_lines', 1, 5, 2).
python_function('imgl/web/agent.py', '_history_lines', 2, 4, 3).
python_function('imgl/web/agent.py', 'pick_agent_action', 3, 20, 14).
python_function('imgl/web/agent.py', '_parse_agent_json', 1, 6, 7).
python_function('imgl/web/app.py', 'create_app', 0, 4, 38).
python_function('imgl/web/thumbs.py', '_clamp_box', 1, 3, 2).
python_function('imgl/web/thumbs.py', 'crop_bbox_png', 2, 2, 12).
python_function('imgl/web/thumbs.py', 'window_bbox_dict', 1, 1, 0).
python_function('imgl/window_scope.py', 'is_monolithic_scene', 1, 2, 2).
python_function('imgl/window_scope.py', 'apply_discovered_windows', 1, 1, 3).
python_function('imgl/window_scope.py', 'discover_windows', 1, 2, 3).
python_function('imgl/window_scope.py', 'summarize_windows', 1, 6, 7).
python_function('imgl/window_scope.py', 'format_window_picker', 1, 4, 4).
python_function('imgl/window_scope.py', 'get_discovered_window', 2, 10, 6).
python_function('imgl/window_scope.py', 'scene_for_window', 2, 4, 6).
python_function('imgl/window_scope.py', 'crop_window_image', 2, 1, 7).
python_function('imgl/window_scope.py', 'export_window_crop', 2, 3, 7).
python_function('imgl/window_scope.py', 'default_window_annotated_path', 2, 2, 3).
python_function('imgl/window_scope.py', '_split_monolithic_window', 1, 8, 12).
python_function('imgl/window_scope.py', '_collect_elements', 1, 2, 1).
python_function('imgl/window_scope.py', '_detect_layout_mode', 2, 12, 6).
python_function('imgl/window_scope.py', '_split_side_by_side', 2, 2, 3).
python_function('imgl/window_scope.py', '_split_stacked', 2, 6, 8).
python_function('imgl/window_scope.py', '_image_gutter_candidates', 2, 14, 11).
python_function('imgl/window_scope.py', '_element_gap_gutters', 2, 6, 8).
python_function('imgl/window_scope.py', '_regions_from_balanced_gutters', 3, 18, 11).
python_function('imgl/window_scope.py', '_split_by_element_y_gaps', 2, 10, 9).
python_function('imgl/window_scope.py', '_best_vertical_split', 2, 12, 7).
python_function('imgl/window_scope.py', '_region_id_for_boxes', 3, 7, 0).
python_function('imgl/window_scope.py', '_guess_window_title', 2, 6, 5).
python_function('imgl/window_scope.py', '_shift_elements', 2, 2, 5).
python_function('imgl/window_scope.py', '_shift_ocr_boxes', 2, 2, 3).
python_function('imgl/window_scope.py', '_safe_filename', 1, 6, 4).
python_function('packages/cli2imgl/src/cli2imgl/cli.py', 'main', 1, 6, 11).
python_function('packages/dsl2imgl/src/dsl2imgl/bus.py', '_run_handler', 1, 2, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/bus.py', 'dispatch', 1, 10, 14).
python_function('packages/dsl2imgl/src/dsl2imgl/bus.py', 'execute_dsl_line', 1, 1, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/bus.py', 'execute_dsl', 1, 4, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/bus.py', 'dispatch_json', 1, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/cli.py', 'main', 1, 9, 12).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'validate_payload', 1, 2, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'parse_text', 1, 2, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'envelope_to_bytes', 1, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'envelope_from_bytes', 1, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'envelope_to_json', 1, 1, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'envelope_from_json', 1, 2, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/codec.py', 'roundtrip_text', 1, 1, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', 'split_command', 1, 4, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', 'pick_flag', 2, 3, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', 'parse_line', 1, 44, 11).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', 'to_text', 1, 10, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', '_build_interact_session', 0, 4, 10).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', '_run_prompt_act', 1, 8, 7).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_health', 1, 1, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_capture', 1, 3, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_analyze', 1, 4, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_actions', 1, 4, 8).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_resolve', 1, 7, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_execute', 1, 14, 10).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_body', 2, 31, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'dict_to_envelope', 1, 1, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'envelope_to_dict', 1, 42, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'encode_protobuf', 1, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'decode_protobuf', 1, 1, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'encode_text_to_protobuf', 1, 2, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'decode_protobuf_to_text', 1, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'result_to_pb', 1, 3, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'pb_to_result', 1, 5, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'encode_result_protobuf', 1, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/schema_registry.py', '_load_schemas', 0, 4, 9).
python_function('packages/dsl2imgl/src/dsl2imgl/schema_registry.py', 'schema_for_verb', 1, 2, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/schema_registry.py', 'all_verbs', 0, 1, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/schema_registry.py', 'validate_schemas', 0, 3, 4).
python_function('packages/dsl2imgl/tests/test_dsl2imgl.py', 'test_health', 0, 3, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl.py', 'test_grammar_roundtrip', 0, 6, 2).
python_function('packages/dsl2imgl/tests/test_dsl2imgl.py', 'test_key_dry_run', 0, 3, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl.py', 'test_key_parses_trailing_image_window', 0, 6, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_schema_registry_covers_all_verbs', 0, 6, 3).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_parse_text_validates_health', 0, 2, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_protobuf_roundtrip_type', 0, 5, 3).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_codec_roundtrip_text', 0, 2, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_dispatch_bytes_envelope', 0, 3, 2).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_event_store_append_command', 1, 4, 4).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_command_dispatch_records_event_id', 2, 3, 3).
python_function('packages/mcp2imgl/src/mcp2imgl/cli.py', 'main', 1, 2, 5).
python_function('packages/mcp2imgl/src/mcp2imgl/server.py', 'run_stdio', 0, 2, 10).
python_function('packages/nlp2imgl/src/nlp2imgl/cli.py', 'main', 1, 15, 16).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'default_image_path', 0, 3, 4).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'default_window', 0, 3, 2).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', '_result_to_dict', 1, 4, 6).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'doctor_capture', 1, 2, 3).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'apply_nl_with_diag', 1, 17, 12).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 'use_llm_enabled', 1, 4, 4).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 'to_dsl', 1, 15, 8).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 'apply_nl', 1, 5, 4).
python_function('packages/rest2imgl/src/rest2imgl/app.py', 'create_app', 0, 1, 20).
python_function('packages/rest2imgl/src/rest2imgl/cli.py', 'main', 1, 2, 7).
python_function('packages/uri2imgl/src/uri2imgl/cli.py', 'main', 1, 4, 11).
python_function('packages/uri2imgl/src/uri2imgl/decode.py', 'uri_to_dsl', 1, 18, 7).
python_function('tests/test_actions.py', '_dialog_scene', 0, 1, 4).
python_function('tests/test_actions.py', 'test_find_button_by_text', 0, 3, 4).
python_function('tests/test_actions.py', 'test_find_input_by_label', 0, 3, 3).
python_function('tests/test_actions.py', 'test_click_coords', 0, 3, 4).
python_function('tests/test_actions.py', 'test_click_action', 0, 6, 3).
python_function('tests/test_actions.py', 'test_type_into_by_label', 0, 6, 3).
python_function('tests/test_actions.py', 'test_find_in_window', 0, 2, 4).
python_function('tests/test_actions.py', 'test_find_one_not_found', 0, 2, 3).
python_function('tests/test_actions.py', 'test_click_raises_when_missing', 0, 1, 4).
python_function('tests/test_actions.py', 'test_list_actions', 0, 4, 4).
python_function('tests/test_actions.py', 'test_cli_find_command', 2, 3, 9).
python_function('tests/test_annotate.py', '_scene', 0, 1, 4).
python_function('tests/test_annotate.py', 'test_default_annotated_path', 0, 2, 2).
python_function('tests/test_annotate.py', 'test_write_annotated_image', 1, 3, 8).
python_function('tests/test_annotate.py', 'test_nlp2uri_mapa', 0, 3, 1).
python_function('tests/test_autodiag.py', 'test_image_freshness_sidecar', 1, 3, 5).
python_function('tests/test_autodiag.py', 'test_verify_capture_updated_fails_on_stale', 1, 1, 4).
python_function('tests/test_autodiag.py', 'test_build_execute_report_json', 0, 3, 2).
python_function('tests/test_autodiag.py', 'test_diagnose_capture_stale', 2, 3, 5).
python_function('tests/test_autodiag.py', 'test_is_valid_png_rejects_empty', 1, 2, 4).
python_function('tests/test_autodiag.py', 'test_vql_cache_path_names', 0, 3, 2).
python_function('tests/test_capture_paths.py', 'test_resolve_image_path_absolute', 1, 2, 3).
python_function('tests/test_capture_paths.py', 'test_resolve_image_path_relative', 2, 2, 5).
python_function('tests/test_capture_paths.py', 'test_resolve_image_path_not_found', 2, 1, 3).
python_function('tests/test_capture_paths.py', 'test_resolve_image_path_optional', 0, 3, 1).
python_function('tests/test_capture_paths.py', 'test_cli_missing_image_friendly_error', 2, 4, 3).
python_function('tests/test_capture_paths.py', 'test_capture_default_path', 1, 2, 1).
python_function('tests/test_capture_paths.py', 'test_cli_vql_aborts_on_blank', 1, 2, 4).
python_function('tests/test_capture_paths.py', 'test_cli_vql_allows_blank_with_flag', 1, 2, 6).
python_function('tests/test_capture_paths.py', 'test_capture_screen_with_mock_vql', 1, 2, 5).
python_function('tests/test_catalog_filter.py', '_noisy_scene', 0, 1, 4).
python_function('tests/test_catalog_filter.py', 'test_filter_catalog_drops_code_and_generic', 0, 8, 7).
python_function('tests/test_catalog_filter.py', 'test_build_interactive_catalog_filtered_by_default', 0, 3, 4).
python_function('tests/test_catalog_interact.py', '_dialog_scene', 0, 1, 4).
python_function('tests/test_catalog_interact.py', 'test_build_interactive_catalog', 0, 9, 4).
python_function('tests/test_catalog_interact.py', 'test_format_catalog_table_contains_indices', 0, 4, 3).
python_function('tests/test_catalog_interact.py', 'test_prompt_to_imgl_uri_click_polish', 0, 6, 3).
python_function('tests/test_catalog_interact.py', 'test_prompt_to_imgl_uri_type_polish', 0, 4, 1).
python_function('tests/test_catalog_interact.py', 'test_prompt_to_imgl_uri_number', 0, 3, 3).
python_function('tests/test_catalog_interact.py', 'test_resolve_imgl_uri_click', 0, 4, 5).
python_function('tests/test_catalog_interact.py', 'test_resolve_imgl_uri_list', 0, 4, 5).
python_function('tests/test_catalog_interact.py', 'test_resolve_imgl_uri_type', 0, 4, 5).
python_function('tests/test_catalog_interact.py', 'test_catalog_input_number_is_click', 0, 7, 5).
python_function('tests/test_catalog_interact.py', 'test_interactive_shell_quit', 1, 3, 5).
python_function('tests/test_diagnose.py', '_black_image', 2, 1, 2).
python_function('tests/test_diagnose.py', '_ui_like_image', 1, 2, 7).
python_function('tests/test_diagnose.py', 'test_worth_analyzing_blank_scene', 0, 2, 1).
python_function('tests/test_diagnose.py', 'test_worth_analyzing_ui_scene', 0, 2, 1).
python_function('tests/test_diagnose.py', 'test_diagnose_black_image_fallback', 1, 4, 5).
python_function('tests/test_diagnose.py', 'test_diagnose_with_img2nl_black', 1, 4, 6).
python_function('tests/test_diagnose.py', 'test_diagnose_with_img2nl_ui', 1, 3, 6).
python_function('tests/test_diagnose.py', 'test_pipeline_skip_blank_raises', 1, 1, 5).
python_function('tests/test_diagnose.py', 'test_pipeline_includes_content_metadata', 1, 4, 5).
python_function('tests/test_diagnose.py', 'test_cli_diagnose_command', 2, 3, 7).
python_function('tests/test_execute_key.py', 'test_normalize_keys', 0, 3, 1).
python_function('tests/test_execute_key.py', 'test_execute_key_dry_run', 0, 3, 1).
python_function('tests/test_export.py', '_make_dialog_fixture', 1, 2, 8).
python_function('tests/test_export.py', '_sample_scene', 0, 1, 4).
python_function('tests/test_export.py', 'test_scene_to_html_structure', 0, 11, 2).
python_function('tests/test_export.py', 'test_scene_to_html_embed_image', 0, 3, 2).
python_function('tests/test_export.py', 'test_scene_to_html_escapes_special_chars', 0, 4, 5).
python_function('tests/test_export.py', 'test_scene_to_svg_wireframe', 0, 7, 3).
python_function('tests/test_export.py', 'test_scene_to_svg_overlay', 0, 3, 2).
python_function('tests/test_export.py', 'test_scene_to_svg_invalid_mode', 0, 1, 3).
python_function('tests/test_export.py', 'test_cli_html_command', 2, 4, 8).
python_function('tests/test_export.py', 'test_cli_svg_command_writes_file', 1, 5, 8).
python_function('tests/test_export.py', 'test_cli_svg_wireframe_default', 2, 3, 7).
python_function('tests/test_imgl.py', '_make_text_image', 2, 2, 7).
python_function('tests/test_imgl.py', 'test_import', 0, 2, 0).
python_function('tests/test_imgl.py', 'test_bbox_as_xyxy_and_contains', 0, 4, 3).
python_function('tests/test_imgl.py', 'test_scene_roundtrip_json', 0, 8, 8).
python_function('tests/test_imgl.py', 'test_scene_from_dict', 0, 3, 1).
python_function('tests/test_imgl.py', 'test_preprocess_resize', 0, 3, 5).
python_function('tests/test_imgl.py', 'test_analyze_with_mocked_ocr', 1, 10, 8).
python_function('tests/test_imgl.py', 'test_analyze_e2e_with_tesseract', 1, 6, 8).
python_function('tests/test_imgl.py', 'test_cli_analyze_stdout', 2, 4, 9).
python_function('tests/test_imgl.py', 'test_cli_analyze_output_file', 1, 4, 8).
python_function('tests/test_layout_classify.py', '_font', 1, 2, 2).
python_function('tests/test_layout_classify.py', '_make_dialog_fixture', 1, 1, 7).
python_function('tests/test_layout_classify.py', 'test_iou_and_center_in', 0, 4, 3).
python_function('tests/test_layout_classify.py', 'test_build_windows_fallback', 0, 4, 2).
python_function('tests/test_layout_classify.py', 'test_build_windows_from_panels', 0, 3, 4).
python_function('tests/test_layout_classify.py', 'test_find_containing_window', 0, 3, 3).
python_function('tests/test_layout_classify.py', 'test_extract_window_titles', 0, 2, 5).
python_function('tests/test_layout_classify.py', 'test_classify_button_with_geometry', 0, 7, 7).
python_function('tests/test_layout_classify.py', 'test_classify_label_input_pair', 0, 7, 5).
python_function('tests/test_layout_classify.py', 'test_detect_ui_elements_on_fixture', 1, 3, 3).
python_function('tests/test_layout_classify.py', 'test_analyze_classifies_dialog', 1, 6, 10).
python_function('tests/test_llm_catalog.py', 'test_load_env_files_reads_dotenv', 2, 3, 6).
python_function('tests/test_llm_catalog.py', 'test_snap_options_to_scene', 0, 3, 6).
python_function('tests/test_llm_catalog.py', 'test_merge_heuristic_inputs_appends_missing_fields', 0, 5, 8).
python_function('tests/test_nlp2imgl_control.py', 'test_apply_nl_with_diag_blocks_stale', 1, 4, 5).
python_function('tests/test_nlp2imgl_llm.py', 'test_to_dsl_adds_llm_flag', 1, 3, 2).
python_function('tests/test_nlp2imgl_llm.py', 'test_to_dsl_explicit_llm_false', 1, 2, 2).
python_function('tests/test_nlp2imgl_llm.py', 'test_use_llm_from_openrouter_key', 1, 2, 3).
python_function('tests/test_nlp2uri_fixes.py', '_scene_with_search_input', 0, 1, 4).
python_function('tests/test_nlp2uri_fixes.py', 'test_click_before_type_for_type_to_search_label', 0, 5, 4).
python_function('tests/test_nlp2uri_fixes.py', 'test_type_into_search_field_from_catalog', 0, 7, 3).
python_function('tests/test_ocr_lang.py', 'test_normalize_url_decoded_lang', 0, 3, 1).
python_function('tests/test_ocr_lang.py', 'test_ocr_lang_attempts_fallback', 0, 3, 1).
python_function('tests/test_scene_cache.py', 'test_scale_scene_to_screen_doubles_coords', 0, 5, 5).
python_function('tests/test_scene_cache.py', 'test_scene_cache_roundtrip', 1, 4, 9).
python_function('tests/test_scene_cache.py', 'test_load_or_analyze_uses_cache', 2, 2, 9).
python_function('tests/test_vdisplay_bridge.py', 'test_suggest_imgl_region_bottom', 0, 2, 1).
python_function('tests/test_vdisplay_bridge.py', 'test_suggest_imgl_region_top', 0, 2, 1).
python_function('tests/test_vdisplay_bridge.py', 'test_correlate_windows_finds_overlap', 0, 4, 2).
python_function('tests/test_vdisplay_bridge.py', 'test_vdisplay_available_is_bool', 0, 2, 2).
python_function('tests/test_vql_export.py', '_sample_scene', 0, 1, 5).
python_function('tests/test_vql_export.py', 'test_scene_to_vql_structure', 0, 19, 3).
python_function('tests/test_vql_export.py', 'test_scene_to_vql_json_roundtrip', 0, 3, 3).
python_function('tests/test_vql_export.py', 'test_write_vql_program', 1, 3, 5).
python_function('tests/test_vql_export.py', 'test_cli_vql_command', 2, 4, 8).
python_function('tests/test_web.py', '_write_ui_fixture', 1, 2, 6).
python_function('tests/test_web.py', 'web_client', 1, 1, 5).
python_function('tests/test_web.py', 'test_health', 1, 3, 2).
python_function('tests/test_web.py', 'test_index_html', 1, 3, 1).
python_function('tests/test_web.py', 'test_state_and_screenshot', 1, 6, 2).
python_function('tests/test_web.py', 'test_act_dry_run_by_index', 1, 5, 4).
python_function('tests/test_web.py', 'test_action_thumb', 1, 5, 4).
python_function('tests/test_web.py', 'test_settings_update', 1, 3, 2).
python_function('tests/test_web.py', 'test_capture_error_returns_state', 2, 5, 4).
python_function('tests/test_web.py', 'test_agent_start_without_llm', 1, 5, 4).
python_function('tests/test_window_scope.py', '_wide_scene', 0, 3, 5).
python_function('tests/test_window_scope.py', 'test_discover_windows_splits_monolithic_scene', 0, 4, 4).
python_function('tests/test_window_scope.py', 'test_scene_for_window_shifts_coordinates', 0, 6, 5).
python_function('tests/test_window_scope.py', 'test_build_catalog_scoped_to_window', 0, 4, 4).
python_function('tests/test_window_scope.py', 'test_export_window_crop_and_preview', 1, 5, 10).
python_function('tests/test_window_scope.py', 'test_stacked_layout_splits_horizontally_not_grid', 1, 6, 13).
python_function('tests/test_window_scope.py', 'test_format_window_picker_lists_regions', 0, 3, 4).
python_function('tests/test_window_scope.py', 'test_single_monitor_region_bottom_alias', 0, 3, 4).

% ── Python Classes ───────────────────────────────────────
python_class('imgl/actions.py', 'ActionTarget').
python_method('ActionTarget', 'center', 0, 1, 0).
python_method('ActionTarget', 'click_coords', 0, 1, 1).
python_method('ActionTarget', 'to_click_action', 0, 2, 2).
python_class('imgl/actions.py', 'TypeAction').
python_method('TypeAction', 'coords', 0, 1, 1).
python_method('TypeAction', 'to_dict', 0, 2, 2).
python_class('imgl/actions.py', 'SceneActions').
python_method('SceneActions', 'find', 1, 21, 9).
python_method('SceneActions', 'find_one', 1, 2, 1).
python_method('SceneActions', 'click', 1, 2, 4).
python_method('SceneActions', 'type_into', 1, 5, 6).
python_method('SceneActions', 'list_actions', 0, 5, 7).
python_class('imgl/actions.py', 'ElementNotFoundError').
python_class('imgl/capture.py', 'CaptureError').
python_class('imgl/capture.py', 'BlankCaptureError').
python_class('imgl/catalog.py', 'InteractiveOption').
python_method('InteractiveOption', 'to_dict', 0, 1, 0).
python_class('imgl/config.py', 'ImglConfig').
python_class('imgl/detect/local.py', 'DetectedUI').
python_class('imgl/diagnose.py', 'BlankImageError').
python_class('imgl/execute.py', 'ExecuteResult').
python_method('ExecuteResult', 'to_dict', 0, 1, 0).
python_class('imgl/interact.py', 'InteractSession').
python_class('imgl/nlp2uri.py', 'ResolvedImglUri').
python_method('ResolvedImglUri', 'to_dict', 0, 1, 0).
python_class('imgl/ocr/base.py', 'OcrBackend').
python_method('OcrBackend', 'run', 1, 1, 0).
python_class('imgl/ocr/tesseract.py', 'TesseractOcr').
python_method('TesseractOcr', 'run', 1, 13, 13).
python_class('imgl/preprocess.py', 'PreprocessedImage').
python_class('imgl/types.py', 'BBox').
python_method('BBox', 'as_xyxy', 0, 1, 0).
python_method('BBox', 'contains', 1, 4, 1).
python_method('BBox', 'to_dict', 0, 4, 0).
python_method('BBox', 'from_xyxy', 5, 1, 2).
python_class('imgl/types.py', 'OcrBox').
python_method('OcrBox', 'to_dict', 0, 4, 2).
python_class('imgl/types.py', 'Element').
python_method('Element', 'to_dict', 0, 4, 2).
python_class('imgl/types.py', 'Window').
python_method('Window', 'to_dict', 0, 4, 1).
python_class('imgl/types.py', 'Scene').
python_method('Scene', 'to_dict', 0, 4, 1).
python_method('Scene', 'from_dict', 2, 5, 8).
python_class('imgl/web/app.py', 'SettingsBody').
python_class('imgl/web/app.py', 'WindowBody').
python_class('imgl/web/app.py', 'ActBody').
python_class('imgl/web/app.py', 'CaptureBody').
python_class('imgl/web/app.py', 'AgentStartBody').
python_class('imgl/web/app.py', 'AgentStepBody').
python_class('imgl/web/session.py', 'StepRecord').
python_method('StepRecord', 'to_dict', 0, 1, 1).
python_class('imgl/web/session.py', 'AgentState').
python_method('AgentState', 'to_dict', 0, 1, 0).
python_class('imgl/web/session.py', 'WebSettings').
python_method('WebSettings', 'to_dict', 0, 1, 0).
python_class('imgl/web/session.py', 'WebSession').
python_method('WebSession', '__post_init__', 0, 1, 4).
python_method('WebSession', 'refresh_catalog', 0, 2, 2).
python_method('WebSession', 'analyze', 0, 1, 6).
python_method('WebSession', 'capture', 0, 1, 4).
python_method('WebSession', 'select_window', 1, 4, 2).
python_method('WebSession', 'resolve_prompt', 1, 2, 3).
python_method('WebSession', 'resolve_index', 1, 1, 2).
python_method('WebSession', 'act', 0, 29, 13).
python_method('WebSession', 'state_dict', 0, 6, 3).
python_method('WebSession', '_refresh_annotated_png', 0, 3, 6).
python_method('WebSession', '_interact_session', 0, 1, 1).
python_method('WebSession', '_step_record', 0, 1, 4).
python_class('imgl/web/session.py', 'SessionManager').
python_method('SessionManager', '__init__', 1, 1, 0).
python_method('SessionManager', 'create', 1, 7, 11).
python_method('SessionManager', 'auto_select_first_window', 0, 3, 2).
python_class('imgl/window_scope.py', 'WindowSummary').
python_method('WindowSummary', 'label', 0, 2, 0).
python_method('WindowSummary', 'bbox', 0, 1, 0).
python_class('packages/dsl2imgl/src/dsl2imgl/events.py', 'StoredEvent').
python_method('StoredEvent', 'to_dict', 0, 1, 1).
python_class('packages/dsl2imgl/src/dsl2imgl/events.py', 'EventStore').
python_method('EventStore', '__init__', 1, 3, 0).
python_method('EventStore', 'for_default', 2, 3, 5).
python_method('EventStore', 'append_command', 2, 2, 7).
python_method('EventStore', '_append_pb', 1, 3, 15).
python_method('EventStore', '_append_jsonl', 1, 3, 16).
python_method('EventStore', 'replay_pb', 0, 4, 13).
python_method('EventStore', 'replay', 0, 6, 12).
python_class('packages/dsl2imgl/src/dsl2imgl/result.py', 'DslResult').
python_method('DslResult', 'to_dict', 0, 1, 0).
python_method('DslResult', 'to_json', 0, 1, 2).
python_class('packages/rest2imgl/src/rest2imgl/app.py', 'NlBody').
python_class('packages/rest2imgl/src/rest2imgl/app.py', 'DoctorBody').

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('SHELL', '').
makefile_target('PIP', '').
makefile_target('PY', '').
makefile_target('IMGL_ROOT', '').
makefile_target('help', '').
makefile_target('venv', '').
makefile_target('install', '').
makefile_target('install-dev', '').
makefile_target('install-control', '').
makefile_target('install-full', '').
makefile_target('install-img2nl', '').
makefile_target('install-vdisplay', '').
makefile_target('test', '').
makefile_target('test-imgl', '').
makefile_target('test-dsl2imgl', '').
makefile_target('capture', '').
makefile_target('capture-interactive', '').
makefile_target('verify-capture', '').
makefile_target('windows', '').
makefile_target('doctor', '').
makefile_target('doctor-full', '').
makefile_target('execute', '').
makefile_target('execute-dry', '').
makefile_target('execute-llm', '').
makefile_target('shot', '').
makefile_target('shot-llm', '').
makefile_target('proto', '').
makefile_target('serve-rest', '').
makefile_target('serve-web', '').
makefile_target('demo-key', '').
makefile_target('demo-nl', '').
makefile_target('demo-chat', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', 'sk-or-v1-...', 'OpenRouter API Key (required for real cost calculation)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Default AI model for cost analysis').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-api-integration.testql.toon.yaml', 'api').
testql_scenario('generated-api-smoke.testql.toon.yaml', 'api').
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-api-integration.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-api-smoke.testql.toon.yaml', 'testql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_interface('api', '').
sumd_interface('mcp', 'stdio').
sumd_interface('cli', 'click').
sumd_interface('cli', '').
sumd_workflow('venv', 'manual').
sumd_workflow_step('venv', 1, 'test -x "$(PY)" || $(PYTHON) -m venv "$(VENV)"').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, '$(PIP) install -e .').
sumd_workflow('install-dev', 'manual').
sumd_workflow_step('install-dev', 1, '$(PIP) install -e ".[dev,llm,capture]"').
sumd_workflow('install-control', 'manual').
sumd_workflow_step('install-control', 1, '$(PIP) install "jsonschema>=4.0" "protobuf>=5.0"').
sumd_workflow_step('install-control', 2, '$(PIP) install -e packages/dsl2imgl packages/nlp2imgl packages/rest2imgl packages/cli2imgl').
sumd_workflow('install-full', 'manual').
sumd_workflow_step('install-full', 1, '$(PIP) install -e ".[web]"').
sumd_workflow_step('install-full', 2, '$(PIP) install "jsonschema>=4.0" "protobuf>=5.0"').
sumd_workflow('install-img2nl', 'manual').
sumd_workflow_step('install-img2nl', 1, '$(IMGL) install img2nl').
sumd_workflow('install-vdisplay', 'manual').
sumd_workflow_step('install-vdisplay', 1, '$(IMGL) install vdisplay').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, '$(PY) -m pytest tests packages/dsl2imgl/tests -q').
sumd_workflow('test-imgl', 'manual').
sumd_workflow_step('test-imgl', 1, '$(PY) -m pytest tests/test_autodiag.py tests/test_vdisplay_bridge.py tests/test_nlp2imgl_control.py -q').
sumd_workflow('test-dsl2imgl', 'manual').
sumd_workflow_step('test-dsl2imgl', 1, '$(PY) -m pytest packages/dsl2imgl/tests -q').
sumd_workflow('capture', 'manual').
sumd_workflow_step('capture', 1, 'test -x "$(PY)" || (echo "Brak $(VENV) — make install-dev" && exit 1)').
sumd_workflow_step('capture', 2, '$(IMGL) capture --smart -o "$(IMGL_IMAGE)"').
sumd_workflow('capture-interactive', 'manual').
sumd_workflow_step('capture-interactive', 1, 'depend target=install-dev').
sumd_workflow_step('capture-interactive', 2, 'rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)"').
sumd_workflow_step('capture-interactive', 3, 'IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture -o "$(IMGL_IMAGE)" --verify').
sumd_workflow_step('capture-interactive', 4, 'rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)"').
sumd_workflow_step('capture-interactive', 5, 'echo "export IMGL_IMAGE=$(IMGL_IMAGE)"').
sumd_workflow('verify-capture', 'manual').
sumd_workflow_step('verify-capture', 1, 'BEFORE=$$(stat -c %Y "$(IMGL_IMAGE)" 2>/dev/null || echo 0)').
sumd_workflow_step('verify-capture', 2, '$(IMGL) verify "$(IMGL_IMAGE)" --before "$$BEFORE"').
sumd_workflow('windows', 'manual').
sumd_workflow_step('windows', 1, '$(IMGL) map --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('doctor', 'manual').
sumd_workflow_step('doctor', 1, '$(IMGL) doctor --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('doctor-full', 'manual').
sumd_workflow_step('doctor-full', 1, '$(IMGL) doctor --full --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('execute', 'manual').
sumd_workflow_step('execute', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1)').
sumd_workflow_step('execute', 2, 'test -n "$(PROMPT)" || (echo "Użycie: make execute PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('execute', 3, '$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('execute-dry', 'manual').
sumd_workflow_step('execute-dry', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1)').
sumd_workflow_step('execute-dry', 2, 'test -n "$(PROMPT)" || (echo "Użycie: make execute-dry PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('execute-dry', 3, '$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --dry-run --format "$(FORMAT)"').
sumd_workflow('execute-llm', 'manual').
sumd_workflow_step('execute-llm', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1)').
sumd_workflow_step('execute-llm', 2, 'test -n "$(PROMPT)" || (echo "Użycie: make execute-llm PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('execute-llm', 3, 'test -n "$$OPENROUTER_API_KEY" || (echo "Brak OPENROUTER_API_KEY — ustaw klucz OpenRouter" && exit 1)').
sumd_workflow_step('execute-llm', 4, '$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --llm --format "$(FORMAT)"').
sumd_workflow('shot', 'manual').
sumd_workflow('shot-llm', 'manual').
sumd_workflow('proto', 'manual').
sumd_workflow_step('proto', 1, 'bash packages/dsl2imgl/scripts/generate-proto.sh').
sumd_workflow('serve-rest', 'manual').
sumd_workflow_step('serve-rest', 1, '$(VENV)/bin/rest2imgl serve --port $(REST_PORT)').
sumd_workflow('serve-web', 'manual').
sumd_workflow_step('serve-web', 1, '$(PY) -m imgl.cli serve --port $(WEB_PORT) --image $(IMGL_IMAGE) --llm --window $(IMGL_WINDOW)').
sumd_workflow('demo-key', 'manual').
sumd_workflow_step('demo-key', 1, '$(VENV)/bin/dsl2imgl exec \'KEY ctrl+Return EXECUTE 0\'').
sumd_workflow('demo-nl', 'manual').
sumd_workflow_step('demo-nl', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak $(IMGL_IMAGE) — uruchom: make capture" && exit 1)').
sumd_workflow_step('demo-nl', 2, '$(VENV)/bin/nlp2imgl apply "wpisz test w Chat input" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW) --dry-run').
sumd_workflow('demo-chat', 'manual').
sumd_workflow_step('demo-chat', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak $(IMGL_IMAGE) — uruchom: make capture" && exit 1)').
sumd_workflow_step('demo-chat', 2, '$(VENV)/bin/nlp2imgl apply "wpisz demo w Chat input" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW) --dry-run').
sumd_workflow_step('demo-chat', 3, '$(VENV)/bin/nlp2imgl apply "naciśnij ctrl+enter" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW) --dry-run').
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

## Intent

Image to Layout — screenshot OCR and semantic UI reconstruction
