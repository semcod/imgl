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
- **version**: `0.7.12`
- **python_requires**: `>=3.10,<3.14`
- **license**: Apache-2.0
- **ai_model**: `openrouter/qwen/qwen3-coder-next`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: pyproject.toml, Makefile, testql(3), app.doql.less, goal.yaml, .env.example, src(33 mod), project/(3 analysis files)

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
  version: 0.7.12
  env: local
```

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
- `IMGL`
- `help`
- `venv`
- `install`
- `install-dev`
- `install-control`
- `install-img2nl`
- `install-vdisplay`
- `install-vql`
- `install-full`
- `capture`
- `capture-interactive`
- `capture-analyze`
- `verify-capture`
- `windows`
- `doctor`
- `doctor-full`
- `execute`
- `execute-dry`
- `execute-llm`
- `shot`
- `test`
- `test-imgl`
- `test-dsl2imgl`
- `proto`
- `serve-rest`
- `serve-web`
- `demo-key`
- `demo-nl`
- `demo-chat`

## Code Analysis

### `project/map.toon.yaml`

```toon markpact:analysis path=project/map.toon.yaml
# imgl | 131f 17446L | python:123,shell:7,less:1 | 2026-06-25
# stats: 738 func | 40 cls | 131 mod | CC̄=4.4 | critical:82 | cycles:0
# alerts[5]: CC test_scene_to_vql_structure=20; CC _derive_current_next=19; CC _process_window_elements=17; CC smart_capture=17; CC apply_nl_with_diag=17
# hotspots[5]: create_app fan=38; analyze fan=20; render_match_overlay_png fan=20; create_app fan=20; scene_to_annotated_image fan=19
# evolution: baseline
# Keys: M=modules, D=details, i=imports, e=exports, c=classes, f=functions, m=methods
M[131]:
  app.doql.less,221
  examples/img2nl-vql-flow.sh,11
  examples/scripts/demo-agent-loop.sh,49
  examples/scripts/demo-github.sh,23
  examples/scripts/demo-nlp2uri.py,80
  examples/scripts/demo-windows.sh,24
  imgl/__init__.py,87
  imgl/__main__.py,7
  imgl/actions.py,282
  imgl/autodiag.py,550
  imgl/capture.py,566
  imgl/capture_provenance.py,115
  imgl/catalog.py,92
  imgl/catalog_filter.py,140
  imgl/catalog_heuristic.py,257
  imgl/catalog_types.py,47
  imgl/classify/__init__.py,6
  imgl/classify/gui_heuristics.py,267
  imgl/cli.py,1004
  imgl/config.py,24
  imgl/control.py,356
  imgl/coords.py,71
  imgl/detect/__init__.py,12
  imgl/detect/img2vql_bridge.py,65
  imgl/detect/local.py,382
  imgl/detect/rectangles.py,97
  imgl/diagnose.py,248
  imgl/execute.py,206
  imgl/export/__init__.py,43
  imgl/export/_escape.py,20
  imgl/export/actuation_layers.py,123
  imgl/export/annotate_export.py,300
  imgl/export/html_export.py,150
  imgl/export/json_export.py,23
  imgl/export/svg_export.py,138
  imgl/export/vql_adapter.py,367
  imgl/freshness.py,152
  imgl/geometry.py,38
  imgl/installs.py,126
  imgl/interact.py,723
  imgl/layout.py,109
  imgl/llm_catalog.py,522
  imgl/nlp2uri.py,294
  imgl/ocr/__init__.py,13
  imgl/ocr/base.py,15
  imgl/ocr/lang.py,33
  imgl/ocr/tesseract.py,95
  imgl/paths.py,42
  imgl/pipeline.py,120
  imgl/preprocess.py,64
  imgl/scene_cache.py,64
  imgl/targets.py,272
  imgl/terminal_md.py,214
  imgl/types.py,171
  imgl/uri.py,119
  imgl/vdisplay_bridge.py,268
  imgl/vdisplay_context.py,81
  imgl/vision_ops.py,278
  imgl/web/__init__.py,11
  imgl/web/agent.py,143
  imgl/web/app.py,287
  imgl/web/session.py,441
  imgl/web/thumbs.py,56
  imgl/window_scope.py,704
  packages/cli2imgl/src/cli2imgl/cli.py,35
  packages/dsl2imgl/scripts/generate-proto.sh,7
  packages/dsl2imgl/src/dsl2imgl/__init__.py,7
  packages/dsl2imgl/src/dsl2imgl/bus.py,111
  packages/dsl2imgl/src/dsl2imgl/cli.py,47
  packages/dsl2imgl/src/dsl2imgl/codec.py,58
  packages/dsl2imgl/src/dsl2imgl/engine.py,6
  packages/dsl2imgl/src/dsl2imgl/events.py,169
  packages/dsl2imgl/src/dsl2imgl/grammar.py,191
  packages/dsl2imgl/src/dsl2imgl/handlers/__init__.py,2
  packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py,235
  packages/dsl2imgl/src/dsl2imgl/pb_codec.py,285
  packages/dsl2imgl/src/dsl2imgl/result.py,35
  packages/dsl2imgl/src/dsl2imgl/schema_registry.py,45
  packages/dsl2imgl/src/dsl2imgl/v1/__init__.py,2
  packages/dsl2imgl/src/dsl2imgl/v1/command_pb2.py,57
  packages/dsl2imgl/src/dsl2imgl/v1/result_pb2.py,40
  packages/dsl2imgl/tests/test_dsl2imgl.py,39
  packages/dsl2imgl/tests/test_dsl2imgl_phase4.py,71
  packages/mcp2imgl/src/mcp2imgl/cli.py,23
  packages/mcp2imgl/src/mcp2imgl/server.py,36
  packages/nlp2imgl/src/nlp2imgl/__init__.py,5
  packages/nlp2imgl/src/nlp2imgl/cli.py,23
  packages/nlp2imgl/src/nlp2imgl/cli_commands.py,72
  packages/nlp2imgl/src/nlp2imgl/cli_parser.py,38
  packages/nlp2imgl/src/nlp2imgl/control.py,151
  packages/nlp2imgl/src/nlp2imgl/to_dsl.py,104
  packages/rest2imgl/src/rest2imgl/app.py,126
  packages/rest2imgl/src/rest2imgl/cli.py,27
  packages/uri2imgl/src/uri2imgl/__init__.py,4
  packages/uri2imgl/src/uri2imgl/cli.py,37
  packages/uri2imgl/src/uri2imgl/decode.py,44
  project.sh,59
  tests/conftest.py,12
  tests/test_actions.py,140
  tests/test_actuation_layers.py,44
  tests/test_annotate.py,59
  tests/test_autodiag.py,149
  tests/test_capture_paths.py,106
  tests/test_capture_provenance.py,201
  tests/test_capture_vdisplay.py,40
  tests/test_capture_vdisplay_priority.py,100
  tests/test_catalog_filter.py,73
  tests/test_catalog_interact.py,200
  tests/test_control_cli.py,144
  tests/test_detect_buttons.py,78
  tests/test_diagnose.py,147
  tests/test_execute_key.py,17
  tests/test_export.py,218
  tests/test_imgl.py,204
  tests/test_installs.py,78
  tests/test_layout_classify.py,176
  tests/test_llm_catalog.py,127
  tests/test_nlp2imgl_cli.py,92
  tests/test_nlp2imgl_control.py,36
  tests/test_nlp2imgl_llm.py,29
  tests/test_nlp2uri_fixes.py,63
  tests/test_ocr_lang.py,17
  tests/test_scene_cache.py,90
  tests/test_targets.py,59
  tests/test_terminal_md.py,49
  tests/test_vdisplay_bridge.py,51
  tests/test_vision_ops.py,84
  tests/test_vql_export.py,120
  tests/test_web.py,121
  tests/test_window_scope.py,221
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
    SceneActions: find(1),_find_labeled_inputs(4),find_one(1),click(1),type_into(1),list_actions(0)  # Find and interact with elements in a Scene.
    ElementNotFoundError:  # Raised when no element matches the query.
    actions(scene)
    _format_query(element_type)
    _text_matches(value;query)
    _iter_elements(scene)
    _window_matches(window;query)
    _find_label_for_input(scene;input_element;window)
  imgl/autodiag.py:
    e: img2nl_root,img2nl_available,_classify_verdict,diagnose_capture,_extract_result_context,build_operation_step,_compact_result,build_execute_report,resolve_cli_output_format,pick_output_format,render_report,_flag_enabled,should_block_blank_capture,should_block_stale_capture,diagnostics_enabled,_yaml_codeblock,_shell_quote,_capture_next_cmd,_derive_stale,_derive_op_failed,_capture_verdict_current_next,_derive_current_next,_capture_payload_section,_markdown_payload,_render_markdown,_overall_verdict,_capture_verdict_hints,_actionable_hints,_compact_features,_scene_class,_parse_coords,_coords_from_action,_parse_typed_text,_parse_keys
    img2nl_root()
    img2nl_available()
    _classify_verdict(diag;is_fresh;scene_class;is_blank;worth)
    diagnose_capture(image_path)
    _extract_result_context(result)
    build_operation_step(result)
    _compact_result(result)
    build_execute_report()
    resolve_cli_output_format()
    pick_output_format(payload;requested)
    render_report(payload;fmt)
    _flag_enabled()
    should_block_blank_capture(capture)
    should_block_stale_capture(capture)
    diagnostics_enabled()
    _yaml_codeblock(data)
    _shell_quote(value)
    _capture_next_cmd(image)
    _derive_stale(capture;image)
    _derive_op_failed(operation)
    _capture_verdict_current_next(capture_verdict;image;capture)
    _derive_current_next(report)
    _capture_payload_section(capture)
    _markdown_payload(report)
    _render_markdown(report)
    _overall_verdict(capture;operation)
    _capture_verdict_hints(capture;image)
    _actionable_hints(report)
    _compact_features(features)
    _scene_class(diag)
    _parse_coords(message)
    _coords_from_action(action)
    _parse_typed_text(message)
    _parse_keys(message)
  imgl/capture.py:
    e: _finalize_capture,last_capture_meta,_prefer_mirror,_vql_capture_enabled,_portal_fallback_enabled,_vdisplay_portal_in_chain_enabled,default_capture_path,_is_wayland,_try_mss_fallback,capture_screen,_screen_recording_denied,_capture_failure_hint,_try_vdisplay_capture,_try_vql_capture,_discard_capture_file,_non_portal_backends,_portal_backends,_try_backend_list,_try_portal_backends,_run_command,_capture_with_gnome_shell,_capture_with_grim,_capture_with_gnome_screenshot,_capture_with_scrot,_portal_python,_portal_script,_parse_portal_output,_capture_with_portal,_capture_with_mss,_is_blank_image,capture_status_message,CaptureError,BlankCaptureError
    CaptureError:  # Raised when screen capture fails.
    BlankCaptureError:  # Raised when capture succeeded but image is empty/black.
    _finalize_capture(path;meta)
    last_capture_meta()
    _prefer_mirror()
    _vql_capture_enabled()
    _portal_fallback_enabled()
    _vdisplay_portal_in_chain_enabled()
    default_capture_path(out)
    _is_wayland()
    _try_mss_fallback(path)
    capture_screen(out)
    _screen_recording_denied(errors)
    _capture_failure_hint()
    _try_vdisplay_capture(path)
    _try_vql_capture(path)
    _discard_capture_file(path)
    _non_portal_backends()
    _portal_backends()
    _try_backend_list(path;backends)
    _try_portal_backends(path)
    _run_command(cmd;path)
    _capture_with_gnome_shell(path)
    _capture_with_grim(path)
    _capture_with_gnome_screenshot(path)
    _capture_with_scrot(path)
    _portal_python()
    _portal_script()
    _parse_portal_output(proc;path)
    _capture_with_portal(path)
    _capture_with_mss(path)
    _is_blank_image(path)
    capture_status_message(path)
  imgl/capture_provenance.py:
    e: capture_meta_path,save_capture_meta,load_capture_meta,enrich_scene_provenance,_correlate_os_windows
    capture_meta_path(image)
    save_capture_meta(image;meta)
    load_capture_meta(image)
    enrich_scene_provenance(scene)
    _correlate_os_windows(scene)
  imgl/catalog.py:
    e: build_interactive_catalog,format_catalog_table,_truncate
    build_interactive_catalog(scene)
    format_catalog_table(options)
    _truncate(value;max_len)
  imgl/catalog_filter.py:
    e: filter_catalog,_renumber,_replace_index_in_uri,_text_quality_check,_keep_element,_element_score,_window_score
    filter_catalog(options)
    _renumber(options)
    _replace_index_in_uri(uri;_index)
    _text_quality_check(text;element_id;category;max_button_chars)
    _keep_element(option)
    _element_score(option)
    _window_score(option)
  imgl/catalog_heuristic.py:
    e: build_heuristic_catalog,infer_input_label,_window_option,_element_option,_find_window,_iter_interactive_elements
    build_heuristic_catalog(scene)
    infer_input_label(element;window)
    _window_option(index;window)
    _element_option(index;element)
    _find_window(scene;window_id)
    _iter_interactive_elements(scene)
  imgl/catalog_types.py:
    e: InteractiveOption
    InteractiveOption: to_dict(0)  # One selectable UI target with mouse/keyboard affordances.
  imgl/classify/__init__.py:
  imgl/classify/gui_heuristics.py:
    e: _process_window_elements,classify_scene_elements,_normalize_confidence,_word_count,_text_or_label,_label_candidates,_match_ocr_to_bbox,_nearest_label,_ocr_inside_frame,_build_inputs
    _process_window_elements(window;window_ocr;geometry_buttons;input_frames;toolbars;used_ocr;label_proximity_px)
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
    e: _add_output_format_flags,_output_format,_add_common_args,build_parser,_write_output,_handle_doctor,_handle_map,_handle_execute,_handle_shot,_handle_verify,_handle_install,_handle_serve,_handle_diagnose,_handle_interact,_handle_windows,_handle_capture,main,_check_blank_before_analyze,_apply_config_overrides,_handle_analyze,_handle_html,_handle_svg,_handle_vql,_handle_annotate,_handle_find,_run_image_command
    _add_output_format_flags(parser)
    _output_format(args)
    _add_common_args(parser)
    build_parser()
    _write_output(content;output)
    _handle_doctor(args;config)
    _handle_map(args;config)
    _handle_execute(args;config)
    _handle_shot(args;config)
    _handle_verify(args;config)
    _handle_install(args;config)
    _handle_serve(args;config)
    _handle_diagnose(args;config)
    _handle_interact(args;config)
    _handle_windows(args;config)
    _handle_capture(args;config)
    main(argv)
    _check_blank_before_analyze(image_path)
    _apply_config_overrides(config;args)
    _handle_analyze(args;image_path;config)
    _handle_html(args;image_path;config)
    _handle_svg(args;image_path;config)
    _handle_vql(args;image_path;config)
    _handle_annotate(args;image_path;config)
    _handle_find(args;image_path;config)
    _run_image_command(args;image_path;config)
  imgl/config.py:
    e: ImglConfig
    ImglConfig:
  imgl/control.py:
    e: default_image_path,default_window,_vql_cache_paths,clear_ocr_cache,screen_usable,_try_vdisplay_fallback,_try_fallback_screen_png,smart_capture,_assert_capture_updated,capture_interactive,verify_capture,run_doctor,run_map,_control_packages_present,_require_nlp2imgl,run_execute,run_shot,install_img2nl,install_vdisplay
    default_image_path()
    default_window()
    _vql_cache_paths(image)
    clear_ocr_cache(image)
    screen_usable(image)
    _try_vdisplay_fallback(path;locale)
    _try_fallback_screen_png(path;locale)
    smart_capture(image)
    _assert_capture_updated(captured;before_mtime;before_size)
    capture_interactive(image)
    verify_capture(image)
    run_doctor(image)
    run_map(image)
    _control_packages_present()
    _require_nlp2imgl()
    run_execute(prompt)
    run_shot(prompt)
    install_img2nl()
    install_vdisplay()
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
    e: _hex_color,_avg_color,_iou_xyxy,_detect_titlebar,_flood_rects,_prepare_button_scan,_neighbor_avg_rgb,_build_contrast_mask,_button_blob_area_limits,_valid_button_blob_size,_scale_blob_rect,_overlaps_seen_button,_button_confidence,_button_role,_button_from_blob_rect,_rank_button_detections,_detect_buttons,_flood_fill_bbox,_detect_panels_simple,_dedupe,detect_ui_elements,DetectedUI
    DetectedUI:
    _hex_color(rgb)
    _avg_color(im;x0;y0;x1;y1)
    _iou_xyxy(a;b)
    _detect_titlebar(im;w;h)
    _flood_rects(mask)
    _prepare_button_scan(im;w;h)
    _neighbor_avg_rgb(pixels)
    _build_contrast_mask(pixels)
    _button_blob_area_limits(sw;sh)
    _valid_button_blob_size(rw;rh)
    _scale_blob_rect(rect;scale)
    _overlaps_seen_button(box;seen_boxes)
    _button_confidence(aspect;bw;bh)
    _button_role(aspect;bw;bh)
    _button_from_blob_rect(im;rect)
    _rank_button_detections(elements)
    _detect_buttons(im;w;h)
    _flood_fill_bbox(cells;start_idx;used;cell_w;cell_h)
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
    e: execute_action,_display_mismatch_warning,_append_display_warning,_execute_xdotool,_execute_ydotool,execute_keys,_normalize_keys,ExecuteResult
    ExecuteResult: to_dict(0)
    execute_action(action)
    _display_mismatch_warning(action)
    _append_display_warning(result;warning)
    _execute_xdotool(kind;x;y;text)
    _execute_ydotool(kind;x;y;text)
    execute_keys(keys)
    _normalize_keys(keys)
  imgl/export/__init__.py:
  imgl/export/_escape.py:
    e: escape_html,escape_xml
    escape_html(text)
    escape_xml(text)
  imgl/export/actuation_layers.py:
    e: bbox_center,bbox_area,layer_from_bbox,_element_layer_from_dict,_window_layers,scene_to_actuation_layers,imgl_result_to_actuation_layers
    bbox_center(bbox)
    bbox_area(bbox)
    layer_from_bbox()
    _element_layer_from_dict(element)
    _window_layers(windows)
    scene_to_actuation_layers(scene)
    imgl_result_to_actuation_layers(imgl)
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
    e: _scene_element_objects,scene_to_vql,scene_to_vql_json,validate_vql_export,write_vql_program,_grid_layer,_bbox_norm,_location_label,_object_from_bbox,_build_contains_relations,_bbox_contains,_window_to_object,_element_to_object,_ocr_to_object
    _scene_element_objects(scene)
    scene_to_vql(scene)
    scene_to_vql_json(scene)
    validate_vql_export(program)
    write_vql_program(scene;path)
    _grid_layer(image_path)
    _bbox_norm(bbox;width;height)
    _location_label(cx;cy;width;height)
    _object_from_bbox()
    _build_contains_relations(objects)
    _bbox_contains(outer;inner)
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
  imgl/installs.py:
    e: _repo_root,vdisplay_available,_auto_install_vdisplay_enabled,ensure_vdisplay,_pip_install_editable,install_img2nl,install_vdisplay,install_vql,install_control
    _repo_root(name;env_key;default)
    vdisplay_available()
    _auto_install_vdisplay_enabled()
    ensure_vdisplay()
    _pip_install_editable(path)
    install_img2nl()
    install_vdisplay()
    install_vql()
    install_control()
  imgl/interact.py:
    e: _build_session_catalog,resolve_imgl_uri,_attach_image_path,_click_by_element_id,_resolve_click,_resolve_type_no_value,_resolve_type_by_element_id,_resolve_type_by_hints,_resolve_type,_annotate_catalog,_select_window,_export_window_previews,_prepare_interactive_session,_show_initial_shell_views,_print_actions_phase_hints,_read_shell_prompt,_handle_resolved_shell_action,run_interactive_shell,_run_shell_loop,describe_resolution,_print_catalog_banner,_handle_window_phase_prompt,InteractSession
    InteractSession:
    _build_session_catalog(session)
    resolve_imgl_uri(uri;session)
    _attach_image_path(payload;session)
    _click_by_element_id(element_id;session)
    _resolve_click(qs;finder;session)
    _resolve_type_no_value(qs;session)
    _resolve_type_by_element_id(element_id;value;session)
    _resolve_type_by_hints(label;text;value;session)
    _resolve_type(qs;finder;session)
    _annotate_catalog(session)
    _select_window(session;window_ref)
    _export_window_previews(session)
    _prepare_interactive_session(image_path)
    _show_initial_shell_views()
    _print_actions_phase_hints()
    _read_shell_prompt(stdin;stderr)
    _handle_resolved_shell_action()
    run_interactive_shell(image_path)
    _run_shell_loop()
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
    e: prompt_to_imgl_uri,_resolve_click_intent,_resolve_type_intent,_delegate_vql_nlp2uri,_find_catalog_by_text,_find_catalog_input,_match_catalog_action,ResolvedImglUri
    ResolvedImglUri: to_dict(0)
    prompt_to_imgl_uri(prompt)
    _resolve_click_intent(click_match;catalog)
    _resolve_type_intent(type_match;catalog)
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
  imgl/targets.py:
    e: _has_chat_token,_bbox_center_x,_bbox_center_y,_parse_layer_fields,normalize_actuation_element,normalize_actuation_elements,_target_result,_find_ask_candidate,_find_chat_token_candidate,_find_panel_candidate,_find_input_candidate,resolve_chat_target,_find_editor_candidate,resolve_editor_target,resolve_actuation_target
    _has_chat_token(text)
    _bbox_center_x(bounds)
    _bbox_center_y(bounds)
    _parse_layer_fields(layer)
    normalize_actuation_element(layer)
    normalize_actuation_elements(layers)
    _target_result(element)
    _find_ask_candidate(els)
    _find_chat_token_candidate(els)
    _find_panel_candidate(els)
    _find_input_candidate(els)
    resolve_chat_target(layers)
    _find_editor_candidate(els)
    resolve_editor_target(layers)
    resolve_actuation_target(layers)
  imgl/terminal_md.py:
    e: _c,stdout_color_enabled,_verdict_color,_highlight_yaml_line,_color_yaml_value,_highlight_bash_line,_highlight_inline,_render_fence_line,_render_normal_line,colorize_markdown,print_report
    _c(name;text)
    stdout_color_enabled()
    _verdict_color(verdict)
    _highlight_yaml_line(line)
    _color_yaml_value(rest)
    _highlight_bash_line(line)
    _highlight_inline(text)
    _render_fence_line(line;fence_lang)
    _render_normal_line(line)
    colorize_markdown(text)
    print_report(text;fmt)
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
    e: vdisplay_available,vdisplay_missing_message,default_display,list_os_windows,list_os_monitors,diagnose_os_display,_norm,find_os_window,suggest_imgl_region,list_vision_windows,_best_vision_match,correlate_windows,_build_report_recommendations,build_window_control_report
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
    _best_vision_match(ox;oy;ow;oh;vision_windows)
    correlate_windows(os_windows;vision_windows)
    _build_report_recommendations()
    build_window_control_report(image)
  imgl/vdisplay_context.py:
    e: from_vdisplay_context,enrich_scene_from_vdisplay,_metadata_from_context
    from_vdisplay_context(payload)
    enrich_scene_from_vdisplay(scene;payload)
    _metadata_from_context(payload)
  imgl/vision_ops.py:
    e: template_available,_png_to_gray_array,_dedupe_matches,match_template_png,diff_png_bytes,_crop_png_region,_confidence_color,render_match_overlay_png,TemplateMatchResult,MatchOverlayItem
    TemplateMatchResult: to_dict(0)
    MatchOverlayItem:
    template_available()
    _png_to_gray_array(png)
    _dedupe_matches(matches)
    match_template_png(png;template_png)
    diff_png_bytes(before;after)
    _crop_png_region(png;region)
    _confidence_color(confidence)
    render_match_overlay_png(png;matches)
  imgl/web/__init__.py:
    e: create_app
    create_app()
  imgl/web/agent.py:
    e: _catalog_lines,_history_lines,pick_agent_action,_resolve_act_response,_parse_agent_json
    _catalog_lines(catalog)
    _history_lines(history;limit)
    pick_agent_action(goal;catalog;history)
    _resolve_act_response(parsed;catalog;reason)
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
    WebSession: __post_init__(0),refresh_catalog(0),analyze(0),capture(0),select_window(1),resolve_prompt(1),resolve_index(1),_fail_act(5),_execute_and_recapture(3),act(0),state_dict(0),_refresh_annotated_png(0),_interact_session(0),_step_record(0)
    SessionManager: __init__(1),create(1),auto_select_first_window(0)  # Single global session for local desktop control.
  imgl/web/thumbs.py:
    e: _clamp_box,crop_bbox_png,window_bbox_dict
    _clamp_box(bbox)
    crop_bbox_png(image_path;bbox)
    window_bbox_dict(window)
  imgl/window_scope.py:
    e: is_monolithic_scene,apply_discovered_windows,discover_windows,summarize_windows,pick_focus_window,should_scope_window,scope_to_focus_window,scope_image_to_focus_window,format_window_picker,get_discovered_window,scene_for_window,crop_window_image,export_window_crop,default_window_annotated_path,_split_monolithic_window,_collect_elements,_detect_layout_mode,_split_side_by_side,_split_stacked,_image_gutter_candidates,_element_gap_gutters,_score_gutter_candidate,_regions_from_balanced_gutters,_split_by_element_y_gaps,_best_vertical_split,_region_id_for_boxes,_guess_window_title,_shift_elements,_shift_ocr_boxes,_safe_filename,WindowSummary
    WindowSummary: label(0),bbox(0)  # One discoverable window region with stats for the picker UI.
    is_monolithic_scene(scene)
    apply_discovered_windows(scene)
    discover_windows(scene)
    summarize_windows(scene)
    pick_focus_window(summaries)
    should_scope_window(scene;summary)
    scope_to_focus_window(image_path;scene)
    scope_image_to_focus_window(image_path)
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
    _score_gutter_candidate(gutter_start;gutter_end;elements;y0;y1;min_region)
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
    e: split_command,pick_flag,_strip_prompt_tokens,_apply_image_window_flags,_parse_capture,_parse_analyze,_parse_actions,_parse_resolve,_parse_click,_parse_type,_parse_key,_parse_execute,_parse_interaction_verb,_parse_agent,parse_line,to_text
    split_command(line)
    pick_flag(tokens;flag)
    _strip_prompt_tokens(rest)
    _apply_image_window_flags(cmd;rest)
    _parse_capture(rest;cmd)
    _parse_analyze(rest;cmd)
    _parse_actions(rest;cmd)
    _parse_resolve(rest;cmd)
    _parse_click(rest;cmd)
    _parse_type(rest;cmd)
    _parse_key(rest;cmd)
    _parse_execute(rest;cmd)
    _parse_interaction_verb(rest;cmd)
    _parse_agent(rest;cmd)
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
    e: _assign_optional_str,_assign_execute_flag,_set_capture_body,_set_analyze_body,_set_actions_body,_set_resolve_body,_set_click_body,_set_type_body,_set_key_body,_set_execute_body,_set_agent_body,_set_body,_dict_optional_str,_dict_execute_flag,_dict_capture_body,_dict_analyze_body,_dict_actions_body,_dict_resolve_body,_dict_click_body,_dict_type_body,_dict_key_body,_dict_execute_body,_dict_agent_body,dict_to_envelope,envelope_to_dict,encode_protobuf,decode_protobuf,encode_text_to_protobuf,decode_protobuf_to_text,result_to_pb,pb_to_result,encode_result_protobuf
    _assign_optional_str(msg;field;cmd;key)
    _assign_execute_flag(msg;cmd)
    _set_capture_body(msg;cmd)
    _set_analyze_body(msg;cmd)
    _set_actions_body(msg;cmd)
    _set_resolve_body(msg;cmd)
    _set_click_body(msg;cmd)
    _set_type_body(msg;cmd)
    _set_key_body(msg;cmd)
    _set_execute_body(msg;cmd)
    _set_agent_body(msg;cmd)
    _set_body(envelope;cmd)
    _dict_optional_str(cmd;msg;key)
    _dict_execute_flag(cmd;msg)
    _dict_capture_body(cmd;msg)
    _dict_analyze_body(cmd;msg)
    _dict_actions_body(cmd;msg)
    _dict_resolve_body(cmd;msg)
    _dict_click_body(cmd;msg)
    _dict_type_body(cmd;msg)
    _dict_key_body(cmd;msg)
    _dict_execute_body(cmd;msg)
    _dict_agent_body(cmd;msg)
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
    e: test_health,test_grammar_roundtrip,test_key_dry_run,test_capture_analyze_flags
    test_health()
    test_grammar_roundtrip()
    test_key_dry_run()
    test_capture_analyze_flags()
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
  packages/nlp2imgl/src/nlp2imgl/cli_commands.py:
    e: output_format,run_to_dsl,run_doctor,_print_apply_payload,run_apply
    output_format(args)
    run_to_dsl(args)
    run_doctor(args)
    _print_apply_payload(payload;fmt)
    run_apply(args)
  packages/nlp2imgl/src/nlp2imgl/cli_parser.py:
    e: build_parser
    build_parser()
  packages/nlp2imgl/src/nlp2imgl/control.py:
    e: default_image_path,default_window,_result_to_dict,doctor_capture,_blocked_capture_response,apply_nl_with_diag
    default_image_path()
    default_window()
    _result_to_dict(result)
    doctor_capture(image)
    _blocked_capture_response()
    apply_nl_with_diag(prompt)
  packages/nlp2imgl/src/nlp2imgl/to_dsl.py:
    e: use_llm_enabled,_dispatch_dsl_command,to_dsl,apply_nl
    use_llm_enabled(explicit)
    _dispatch_dsl_command(text;image;flags;llm_flag)
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
    e: _dsl_click,_dsl_type,uri_to_dsl
    _dsl_click(qs;flags)
    _dsl_type(qs;flags)
    uri_to_dsl(uri)
  tests/conftest.py:
    e: _disable_vdisplay_auto_install
    _disable_vdisplay_auto_install(monkeypatch)
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
  tests/test_actuation_layers.py:
    e: test_scene_to_actuation_layers_flattens_window_elements_and_ocr,test_bbox_area_supports_w_h,test_imgl_result_to_actuation_layers_requires_ok
    test_scene_to_actuation_layers_flattens_window_elements_and_ocr()
    test_bbox_area_supports_w_h()
    test_imgl_result_to_actuation_layers_requires_ok()
  tests/test_annotate.py:
    e: _scene,test_default_annotated_path,test_write_annotated_image,test_nlp2uri_mapa
    _scene()
    test_default_annotated_path()
    test_write_annotated_image(tmp_path)
    test_nlp2uri_mapa()
  tests/test_autodiag.py:
    e: test_image_freshness_sidecar,test_verify_capture_updated_fails_on_stale,test_build_execute_report_json,test_render_report_markdown_uses_yaml_codeblock,test_pick_output_format_defaults_to_markdown,test_build_execute_report_stale_has_current_and_next_cmd,test_diagnose_capture_stale,test_is_valid_png_rejects_empty,test_vql_cache_path_names
    test_image_freshness_sidecar(tmp_path)
    test_verify_capture_updated_fails_on_stale(tmp_path)
    test_build_execute_report_json()
    test_render_report_markdown_uses_yaml_codeblock()
    test_pick_output_format_defaults_to_markdown()
    test_build_execute_report_stale_has_current_and_next_cmd()
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
    test_capture_screen_with_mock_vql(tmp_path;monkeypatch)
  tests/test_capture_provenance.py:
    e: test_save_and_load_capture_meta,test_enrich_scene_attaches_capture_meta,test_scene_to_vql_includes_capture_and_relations,test_execute_display_mismatch_warning,test_execute_display_mismatch_strict,test_enrich_scene_correlates_os_windows,test_clear_vql_cache_keeps_capture_meta,test_finalize_capture_enriches_display
    test_save_and_load_capture_meta(tmp_path)
    test_enrich_scene_attaches_capture_meta(tmp_path)
    test_scene_to_vql_includes_capture_and_relations(tmp_path)
    test_execute_display_mismatch_warning(tmp_path;monkeypatch)
    test_execute_display_mismatch_strict(tmp_path;monkeypatch)
    test_enrich_scene_correlates_os_windows(tmp_path)
    test_clear_vql_cache_keeps_capture_meta(tmp_path)
    test_finalize_capture_enriches_display(monkeypatch;tmp_path)
  tests/test_capture_vdisplay.py:
    e: test_capture_screen_prefers_vdisplay
    test_capture_screen_prefers_vdisplay(tmp_path)
  tests/test_capture_vdisplay_priority.py:
    e: test_capture_prefers_vdisplay_over_portal,test_capture_interactive_uses_mirror_not_portal,test_capture_interactive_portal_fallback_on_wayland
    test_capture_prefers_vdisplay_over_portal(tmp_path;monkeypatch)
    test_capture_interactive_uses_mirror_not_portal(tmp_path)
    test_capture_interactive_portal_fallback_on_wayland(tmp_path;monkeypatch)
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
  tests/test_control_cli.py:
    e: test_default_image_path_env,test_default_window_env,test_run_doctor,test_run_execute_missing_image,test_run_execute_loads_openrouter_key_from_dotenv,test_cli_doctor_help,test_cli_execute_help,test_require_nlp2imgl_auto_installs_from_local_packages,test_cli_default_output_is_markdown
    test_default_image_path_env(monkeypatch;tmp_path)
    test_default_window_env(monkeypatch)
    test_run_doctor(tmp_path;monkeypatch)
    test_run_execute_missing_image(tmp_path;monkeypatch)
    test_run_execute_loads_openrouter_key_from_dotenv(tmp_path;monkeypatch)
    test_cli_doctor_help()
    test_cli_execute_help()
    test_require_nlp2imgl_auto_installs_from_local_packages(monkeypatch)
    test_cli_default_output_is_markdown()
  tests/test_detect_buttons.py:
    e: test_valid_button_blob_size_filters_extremes,test_button_role_classifies_icon_vs_button,test_button_confidence_prefers_typical_toolbar_shape,test_overlaps_seen_button_dedupes_high_iou,test_button_from_blob_rect_returns_none_for_invalid_blob,test_detect_buttons_finds_contrast_blob,test_detect_ui_elements_still_includes_buttons
    test_valid_button_blob_size_filters_extremes()
    test_button_role_classifies_icon_vs_button()
    test_button_confidence_prefers_typical_toolbar_shape()
    test_overlaps_seen_button_dedupes_high_iou()
    test_button_from_blob_rect_returns_none_for_invalid_blob()
    test_detect_buttons_finds_contrast_blob()
    test_detect_ui_elements_still_includes_buttons(tmp_path)
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
  tests/test_installs.py:
    e: test_install_img2nl_missing_repo,test_install_img2nl_calls_pip,test_install_vdisplay_calls_pip,test_install_vql_calls_pip,test_install_control_calls_pip,test_ensure_vdisplay_skips_when_installed,test_ensure_vdisplay_auto_installs
    test_install_img2nl_missing_repo(tmp_path;monkeypatch)
    test_install_img2nl_calls_pip(tmp_path;monkeypatch)
    test_install_vdisplay_calls_pip(tmp_path;monkeypatch)
    test_install_vql_calls_pip(tmp_path;monkeypatch)
    test_install_control_calls_pip()
    test_ensure_vdisplay_skips_when_installed(monkeypatch)
    test_ensure_vdisplay_auto_installs(monkeypatch)
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
  tests/test_nlp2imgl_cli.py:
    e: test_build_parser_registers_subcommands,test_run_to_dsl_prints_line,test_run_apply_uses_json_when_requested,test_run_doctor_exits_nonzero_on_stale_capture,test_main_dispatches_apply
    test_build_parser_registers_subcommands()
    test_run_to_dsl_prints_line(monkeypatch;capsys)
    test_run_apply_uses_json_when_requested(monkeypatch;capsys)
    test_run_doctor_exits_nonzero_on_stale_capture(monkeypatch)
    test_main_dispatches_apply(monkeypatch)
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
  tests/test_targets.py:
    e: test_resolve_chat_prefers_panel_over_send_chat_ocr_label,test_resolve_editor_prefers_window_0,test_resolve_chat_picks_bottom_right_input
    test_resolve_chat_prefers_panel_over_send_chat_ocr_label()
    test_resolve_editor_prefers_window_0()
    test_resolve_chat_picks_bottom_right_input()
  tests/test_terminal_md.py:
    e: test_stdout_color_disabled_with_no_color,test_colorize_markdown_adds_ansi_when_forced,test_colorize_markdown_plain_when_disabled,test_resolve_cli_output_format_flags
    test_stdout_color_disabled_with_no_color(monkeypatch)
    test_colorize_markdown_adds_ansi_when_forced()
    test_colorize_markdown_plain_when_disabled()
    test_resolve_cli_output_format_flags()
  tests/test_vdisplay_bridge.py:
    e: test_suggest_imgl_region_bottom,test_suggest_imgl_region_top,test_correlate_windows_finds_overlap,test_vdisplay_available_is_bool
    test_suggest_imgl_region_bottom()
    test_suggest_imgl_region_top()
    test_correlate_windows_finds_overlap()
    test_vdisplay_available_is_bool()
  tests/test_vision_ops.py:
    e: _tiny_png,test_match_template_png_finds_exact_copy,test_diff_png_bytes_detects_change,test_render_match_overlay_png,test_from_vdisplay_context_metadata_without_image
    _tiny_png()
    test_match_template_png_finds_exact_copy()
    test_diff_png_bytes_detects_change()
    test_render_match_overlay_png()
    test_from_vdisplay_context_metadata_without_image()
  tests/test_vql_export.py:
    e: _sample_scene,test_scene_to_vql_structure,test_scene_to_vql_json_roundtrip,test_write_vql_program,test_validate_vql_export_when_vql_installed,test_cli_vql_command
    _sample_scene()
    test_scene_to_vql_structure()
    test_scene_to_vql_json_roundtrip()
    test_write_vql_program(tmp_path)
    test_validate_vql_export_when_vql_installed()
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
    e: _wide_scene,test_discover_windows_splits_monolithic_scene,test_scene_for_window_shifts_coordinates,test_build_catalog_scoped_to_window,test_export_window_crop_and_preview,test_stacked_layout_splits_horizontally_not_grid,test_format_window_picker_lists_regions,test_single_monitor_region_bottom_alias,test_pick_focus_window_prefers_interactive_region,test_scope_to_focus_window_exports_crop
    _wide_scene()
    test_discover_windows_splits_monolithic_scene()
    test_scene_for_window_shifts_coordinates()
    test_build_catalog_scoped_to_window()
    test_export_window_crop_and_preview(tmp_path)
    test_stacked_layout_splits_horizontally_not_grid(tmp_path)
    test_format_window_picker_lists_regions()
    test_single_monitor_region_bottom_alias()
    test_pick_focus_window_prefers_interactive_region()
    test_scope_to_focus_window_exports_crop(tmp_path)
```

### `project/logic.pl`

```prolog markpact:analysis path=project/logic.pl
% ── Project Metadata ─────────────────────────────────────
project_metadata('imgl', '0.7.12', 'python').

% ── Project Files ────────────────────────────────────────
project_file('app.doql.less', 221, 'less').
project_file('examples/img2nl-vql-flow.sh', 11, 'shell').
project_file('examples/scripts/demo-agent-loop.sh', 49, 'shell').
project_file('examples/scripts/demo-github.sh', 23, 'shell').
project_file('examples/scripts/demo-nlp2uri.py', 80, 'python').
project_file('examples/scripts/demo-windows.sh', 24, 'shell').
project_file('imgl/__init__.py', 87, 'python').
project_file('imgl/__main__.py', 7, 'python').
project_file('imgl/actions.py', 282, 'python').
project_file('imgl/autodiag.py', 550, 'python').
project_file('imgl/capture.py', 566, 'python').
project_file('imgl/capture_provenance.py', 115, 'python').
project_file('imgl/catalog.py', 92, 'python').
project_file('imgl/catalog_filter.py', 140, 'python').
project_file('imgl/catalog_heuristic.py', 257, 'python').
project_file('imgl/catalog_types.py', 47, 'python').
project_file('imgl/classify/__init__.py', 6, 'python').
project_file('imgl/classify/gui_heuristics.py', 267, 'python').
project_file('imgl/cli.py', 1004, 'python').
project_file('imgl/config.py', 24, 'python').
project_file('imgl/control.py', 356, 'python').
project_file('imgl/coords.py', 71, 'python').
project_file('imgl/detect/__init__.py', 12, 'python').
project_file('imgl/detect/img2vql_bridge.py', 65, 'python').
project_file('imgl/detect/local.py', 382, 'python').
project_file('imgl/detect/rectangles.py', 97, 'python').
project_file('imgl/diagnose.py', 248, 'python').
project_file('imgl/execute.py', 206, 'python').
project_file('imgl/export/__init__.py', 43, 'python').
project_file('imgl/export/_escape.py', 20, 'python').
project_file('imgl/export/actuation_layers.py', 123, 'python').
project_file('imgl/export/annotate_export.py', 300, 'python').
project_file('imgl/export/html_export.py', 150, 'python').
project_file('imgl/export/json_export.py', 23, 'python').
project_file('imgl/export/svg_export.py', 138, 'python').
project_file('imgl/export/vql_adapter.py', 367, 'python').
project_file('imgl/freshness.py', 152, 'python').
project_file('imgl/geometry.py', 38, 'python').
project_file('imgl/installs.py', 126, 'python').
project_file('imgl/interact.py', 723, 'python').
project_file('imgl/layout.py', 109, 'python').
project_file('imgl/llm_catalog.py', 522, 'python').
project_file('imgl/nlp2uri.py', 294, 'python').
project_file('imgl/ocr/__init__.py', 13, 'python').
project_file('imgl/ocr/base.py', 15, 'python').
project_file('imgl/ocr/lang.py', 33, 'python').
project_file('imgl/ocr/tesseract.py', 95, 'python').
project_file('imgl/paths.py', 42, 'python').
project_file('imgl/pipeline.py', 120, 'python').
project_file('imgl/preprocess.py', 64, 'python').
project_file('imgl/scene_cache.py', 64, 'python').
project_file('imgl/targets.py', 272, 'python').
project_file('imgl/terminal_md.py', 214, 'python').
project_file('imgl/types.py', 171, 'python').
project_file('imgl/uri.py', 119, 'python').
project_file('imgl/vdisplay_bridge.py', 268, 'python').
project_file('imgl/vdisplay_context.py', 81, 'python').
project_file('imgl/vision_ops.py', 278, 'python').
project_file('imgl/web/__init__.py', 11, 'python').
project_file('imgl/web/agent.py', 143, 'python').
project_file('imgl/web/app.py', 287, 'python').
project_file('imgl/web/session.py', 441, 'python').
project_file('imgl/web/thumbs.py', 56, 'python').
project_file('imgl/window_scope.py', 704, 'python').
project_file('packages/cli2imgl/src/cli2imgl/cli.py', 35, 'python').
project_file('packages/dsl2imgl/scripts/generate-proto.sh', 7, 'shell').
project_file('packages/dsl2imgl/src/dsl2imgl/__init__.py', 7, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/bus.py', 111, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/cli.py', 47, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/codec.py', 58, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/engine.py', 6, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/events.py', 169, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/grammar.py', 191, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/handlers/__init__.py', 2, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 235, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 285, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/result.py', 35, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/schema_registry.py', 45, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/v1/__init__.py', 2, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/v1/command_pb2.py', 57, 'python').
project_file('packages/dsl2imgl/src/dsl2imgl/v1/result_pb2.py', 40, 'python').
project_file('packages/dsl2imgl/tests/test_dsl2imgl.py', 39, 'python').
project_file('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 71, 'python').
project_file('packages/mcp2imgl/src/mcp2imgl/cli.py', 23, 'python').
project_file('packages/mcp2imgl/src/mcp2imgl/server.py', 36, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/__init__.py', 5, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/cli.py', 23, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/cli_commands.py', 72, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/cli_parser.py', 38, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/control.py', 151, 'python').
project_file('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 104, 'python').
project_file('packages/rest2imgl/src/rest2imgl/app.py', 126, 'python').
project_file('packages/rest2imgl/src/rest2imgl/cli.py', 27, 'python').
project_file('packages/uri2imgl/src/uri2imgl/__init__.py', 4, 'python').
project_file('packages/uri2imgl/src/uri2imgl/cli.py', 37, 'python').
project_file('packages/uri2imgl/src/uri2imgl/decode.py', 44, 'python').
project_file('project.sh', 59, 'shell').
project_file('tests/conftest.py', 12, 'python').
project_file('tests/test_actions.py', 140, 'python').
project_file('tests/test_actuation_layers.py', 44, 'python').
project_file('tests/test_annotate.py', 59, 'python').
project_file('tests/test_autodiag.py', 149, 'python').
project_file('tests/test_capture_paths.py', 106, 'python').
project_file('tests/test_capture_provenance.py', 201, 'python').
project_file('tests/test_capture_vdisplay.py', 40, 'python').
project_file('tests/test_capture_vdisplay_priority.py', 100, 'python').
project_file('tests/test_catalog_filter.py', 73, 'python').
project_file('tests/test_catalog_interact.py', 200, 'python').
project_file('tests/test_control_cli.py', 144, 'python').
project_file('tests/test_detect_buttons.py', 78, 'python').
project_file('tests/test_diagnose.py', 147, 'python').
project_file('tests/test_execute_key.py', 17, 'python').
project_file('tests/test_export.py', 218, 'python').
project_file('tests/test_imgl.py', 204, 'python').
project_file('tests/test_installs.py', 78, 'python').
project_file('tests/test_layout_classify.py', 176, 'python').
project_file('tests/test_llm_catalog.py', 127, 'python').
project_file('tests/test_nlp2imgl_cli.py', 92, 'python').
project_file('tests/test_nlp2imgl_control.py', 36, 'python').
project_file('tests/test_nlp2imgl_llm.py', 29, 'python').
project_file('tests/test_nlp2uri_fixes.py', 63, 'python').
project_file('tests/test_ocr_lang.py', 17, 'python').
project_file('tests/test_scene_cache.py', 90, 'python').
project_file('tests/test_targets.py', 59, 'python').
project_file('tests/test_terminal_md.py', 49, 'python').
project_file('tests/test_vdisplay_bridge.py', 51, 'python').
project_file('tests/test_vision_ops.py', 84, 'python').
project_file('tests/test_vql_export.py', 120, 'python').
project_file('tests/test_web.py', 121, 'python').
project_file('tests/test_window_scope.py', 221, 'python').
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
python_function('imgl/autodiag.py', '_classify_verdict', 5, 8, 1).
python_function('imgl/autodiag.py', 'diagnose_capture', 1, 9, 17).
python_function('imgl/autodiag.py', '_extract_result_context', 1, 8, 3).
python_function('imgl/autodiag.py', 'build_operation_step', 1, 12, 9).
python_function('imgl/autodiag.py', '_compact_result', 1, 6, 3).
python_function('imgl/autodiag.py', 'build_execute_report', 0, 8, 7).
python_function('imgl/autodiag.py', 'resolve_cli_output_format', 0, 7, 1).
python_function('imgl/autodiag.py', 'pick_output_format', 2, 2, 0).
python_function('imgl/autodiag.py', 'render_report', 2, 3, 4).
python_function('imgl/autodiag.py', '_flag_enabled', 0, 3, 3).
python_function('imgl/autodiag.py', 'should_block_blank_capture', 1, 2, 2).
python_function('imgl/autodiag.py', 'should_block_stale_capture', 1, 3, 2).
python_function('imgl/autodiag.py', 'diagnostics_enabled', 0, 1, 1).
python_function('imgl/autodiag.py', '_yaml_codeblock', 1, 1, 2).
python_function('imgl/autodiag.py', '_shell_quote', 1, 3, 2).
python_function('imgl/autodiag.py', '_capture_next_cmd', 1, 1, 1).
python_function('imgl/autodiag.py', '_derive_stale', 2, 2, 2).
python_function('imgl/autodiag.py', '_derive_op_failed', 1, 9, 4).
python_function('imgl/autodiag.py', '_capture_verdict_current_next', 3, 6, 2).
python_function('imgl/autodiag.py', '_derive_current_next', 1, 19, 8).
python_function('imgl/autodiag.py', '_capture_payload_section', 1, 6, 1).
python_function('imgl/autodiag.py', '_markdown_payload', 1, 14, 2).
python_function('imgl/autodiag.py', '_render_markdown', 1, 6, 7).
python_function('imgl/autodiag.py', '_overall_verdict', 2, 10, 1).
python_function('imgl/autodiag.py', '_capture_verdict_hints', 2, 6, 3).
python_function('imgl/autodiag.py', '_actionable_hints', 1, 14, 5).
python_function('imgl/autodiag.py', '_compact_features', 1, 6, 1).
python_function('imgl/autodiag.py', '_scene_class', 1, 2, 2).
python_function('imgl/autodiag.py', '_parse_coords', 1, 2, 3).
python_function('imgl/autodiag.py', '_coords_from_action', 1, 3, 1).
python_function('imgl/autodiag.py', '_parse_typed_text', 1, 2, 2).
python_function('imgl/autodiag.py', '_parse_keys', 1, 2, 3).
python_function('imgl/capture.py', '_finalize_capture', 2, 6, 4).
python_function('imgl/capture.py', 'last_capture_meta', 0, 1, 1).
python_function('imgl/capture.py', '_prefer_mirror', 0, 1, 3).
python_function('imgl/capture.py', '_vql_capture_enabled', 0, 1, 3).
python_function('imgl/capture.py', '_portal_fallback_enabled', 0, 2, 4).
python_function('imgl/capture.py', '_vdisplay_portal_in_chain_enabled', 0, 2, 4).
python_function('imgl/capture.py', 'default_capture_path', 1, 2, 6).
python_function('imgl/capture.py', '_is_wayland', 0, 3, 3).
python_function('imgl/capture.py', '_try_mss_fallback', 1, 6, 5).
python_function('imgl/capture.py', 'capture_screen', 1, 16, 16).
python_function('imgl/capture.py', '_screen_recording_denied', 1, 2, 2).
python_function('imgl/capture.py', '_capture_failure_hint', 0, 5, 2).
python_function('imgl/capture.py', '_try_vdisplay_capture', 1, 10, 12).
python_function('imgl/capture.py', '_try_vql_capture', 1, 8, 9).
python_function('imgl/capture.py', '_discard_capture_file', 1, 3, 3).
python_function('imgl/capture.py', '_non_portal_backends', 0, 2, 2).
python_function('imgl/capture.py', '_portal_backends', 0, 1, 1).
python_function('imgl/capture.py', '_try_backend_list', 2, 8, 7).
python_function('imgl/capture.py', '_try_portal_backends', 1, 1, 2).
python_function('imgl/capture.py', '_run_command', 2, 3, 4).
python_function('imgl/capture.py', '_capture_with_gnome_shell', 1, 11, 9).
python_function('imgl/capture.py', '_capture_with_grim', 1, 10, 7).
python_function('imgl/capture.py', '_capture_with_gnome_screenshot', 1, 2, 3).
python_function('imgl/capture.py', '_capture_with_scrot', 1, 2, 3).
python_function('imgl/capture.py', '_portal_python', 0, 7, 5).
python_function('imgl/capture.py', '_portal_script', 0, 5, 3).
python_function('imgl/capture.py', '_parse_portal_output', 2, 11, 6).
python_function('imgl/capture.py', '_capture_with_portal', 1, 6, 9).
python_function('imgl/capture.py', '_capture_with_mss', 1, 1, 8).
python_function('imgl/capture.py', '_is_blank_image', 1, 6, 13).
python_function('imgl/capture.py', 'capture_status_message', 1, 2, 1).
python_function('imgl/capture_provenance.py', 'capture_meta_path', 1, 1, 2).
python_function('imgl/capture_provenance.py', 'save_capture_meta', 2, 1, 7).
python_function('imgl/capture_provenance.py', 'load_capture_meta', 1, 4, 5).
python_function('imgl/capture_provenance.py', 'enrich_scene_provenance', 1, 4, 4).
python_function('imgl/capture_provenance.py', '_correlate_os_windows', 1, 10, 7).
python_function('imgl/catalog.py', 'build_interactive_catalog', 1, 3, 3).
python_function('imgl/catalog.py', 'format_catalog_table', 1, 8, 4).
python_function('imgl/catalog.py', '_truncate', 2, 2, 3).
python_function('imgl/catalog_filter.py', 'filter_catalog', 1, 8, 6).
python_function('imgl/catalog_filter.py', '_renumber', 1, 2, 4).
python_function('imgl/catalog_filter.py', '_replace_index_in_uri', 2, 1, 0).
python_function('imgl/catalog_filter.py', '_text_quality_check', 4, 10, 6).
python_function('imgl/catalog_filter.py', '_keep_element', 1, 7, 4).
python_function('imgl/catalog_filter.py', '_element_score', 1, 9, 4).
python_function('imgl/catalog_filter.py', '_window_score', 1, 5, 1).
python_function('imgl/catalog_heuristic.py', 'build_heuristic_catalog', 1, 10, 8).
python_function('imgl/catalog_heuristic.py', 'infer_input_label', 2, 13, 0).
python_function('imgl/catalog_heuristic.py', '_window_option', 2, 2, 4).
python_function('imgl/catalog_heuristic.py', '_element_option', 2, 13, 9).
python_function('imgl/catalog_heuristic.py', '_find_window', 2, 2, 1).
python_function('imgl/catalog_heuristic.py', '_iter_interactive_elements', 1, 9, 1).
python_function('imgl/classify/gui_heuristics.py', '_process_window_elements', 7, 17, 13).
python_function('imgl/classify/gui_heuristics.py', 'classify_scene_elements', 4, 11, 8).
python_function('imgl/classify/gui_heuristics.py', '_normalize_confidence', 1, 2, 0).
python_function('imgl/classify/gui_heuristics.py', '_word_count', 1, 1, 2).
python_function('imgl/classify/gui_heuristics.py', '_text_or_label', 1, 7, 4).
python_function('imgl/classify/gui_heuristics.py', '_label_candidates', 2, 5, 3).
python_function('imgl/classify/gui_heuristics.py', '_match_ocr_to_bbox', 3, 5, 3).
python_function('imgl/classify/gui_heuristics.py', '_nearest_label', 3, 7, 3).
python_function('imgl/classify/gui_heuristics.py', '_ocr_inside_frame', 3, 4, 1).
python_function('imgl/classify/gui_heuristics.py', '_build_inputs', 0, 7, 7).
python_function('imgl/cli.py', '_add_output_format_flags', 1, 1, 2).
python_function('imgl/cli.py', '_output_format', 1, 1, 1).
python_function('imgl/cli.py', '_add_common_args', 1, 1, 1).
python_function('imgl/cli.py', 'build_parser', 0, 1, 7).
python_function('imgl/cli.py', '_write_output', 2, 2, 2).
python_function('imgl/cli.py', '_handle_doctor', 2, 2, 4).
python_function('imgl/cli.py', '_handle_map', 2, 2, 4).
python_function('imgl/cli.py', '_handle_execute', 2, 4, 6).
python_function('imgl/cli.py', '_handle_shot', 2, 3, 6).
python_function('imgl/cli.py', '_handle_verify', 2, 3, 3).
python_function('imgl/cli.py', '_handle_install', 2, 6, 6).
python_function('imgl/cli.py', '_handle_serve', 2, 10, 10).
python_function('imgl/cli.py', '_handle_diagnose', 2, 4, 8).
python_function('imgl/cli.py', '_handle_interact', 2, 3, 6).
python_function('imgl/cli.py', '_handle_windows', 2, 11, 18).
python_function('imgl/cli.py', '_handle_capture', 2, 13, 14).
python_function('imgl/cli.py', 'main', 1, 4, 9).
python_function('imgl/cli.py', '_check_blank_before_analyze', 1, 5, 4).
python_function('imgl/cli.py', '_apply_config_overrides', 2, 2, 1).
python_function('imgl/cli.py', '_handle_analyze', 3, 1, 3).
python_function('imgl/cli.py', '_handle_html', 3, 1, 3).
python_function('imgl/cli.py', '_handle_svg', 3, 3, 4).
python_function('imgl/cli.py', '_handle_vql', 3, 2, 5).
python_function('imgl/cli.py', '_handle_annotate', 3, 4, 10).
python_function('imgl/cli.py', '_handle_find', 3, 6, 11).
python_function('imgl/cli.py', '_run_image_command', 3, 3, 5).
python_function('imgl/control.py', 'default_image_path', 0, 3, 5).
python_function('imgl/control.py', 'default_window', 0, 3, 2).
python_function('imgl/control.py', '_vql_cache_paths', 1, 1, 1).
python_function('imgl/control.py', 'clear_ocr_cache', 1, 1, 1).
python_function('imgl/control.py', 'screen_usable', 1, 2, 3).
python_function('imgl/control.py', '_try_vdisplay_fallback', 2, 5, 6).
python_function('imgl/control.py', '_try_fallback_screen_png', 2, 5, 10).
python_function('imgl/control.py', 'smart_capture', 1, 17, 15).
python_function('imgl/control.py', '_assert_capture_updated', 3, 6, 4).
python_function('imgl/control.py', 'capture_interactive', 1, 11, 16).
python_function('imgl/control.py', 'verify_capture', 1, 4, 6).
python_function('imgl/control.py', 'run_doctor', 1, 7, 7).
python_function('imgl/control.py', 'run_map', 1, 3, 5).
python_function('imgl/control.py', '_control_packages_present', 0, 2, 3).
python_function('imgl/control.py', '_require_nlp2imgl', 0, 4, 3).
python_function('imgl/control.py', 'run_execute', 1, 13, 16).
python_function('imgl/control.py', 'run_shot', 1, 1, 2).
python_function('imgl/control.py', 'install_img2nl', 0, 1, 1).
python_function('imgl/control.py', 'install_vdisplay', 0, 1, 1).
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
python_function('imgl/detect/local.py', '_prepare_button_scan', 3, 1, 5).
python_function('imgl/detect/local.py', '_neighbor_avg_rgb', 1, 7, 5).
python_function('imgl/detect/local.py', '_build_contrast_mask', 1, 5, 5).
python_function('imgl/detect/local.py', '_button_blob_area_limits', 2, 1, 2).
python_function('imgl/detect/local.py', '_valid_button_blob_size', 2, 3, 0).
python_function('imgl/detect/local.py', '_scale_blob_rect', 2, 1, 1).
python_function('imgl/detect/local.py', '_overlaps_seen_button', 2, 2, 2).
python_function('imgl/detect/local.py', '_button_confidence', 3, 4, 0).
python_function('imgl/detect/local.py', '_button_role', 3, 4, 0).
python_function('imgl/detect/local.py', '_button_from_blob_rect', 2, 3, 11).
python_function('imgl/detect/local.py', '_rank_button_detections', 1, 1, 1).
python_function('imgl/detect/local.py', '_detect_buttons', 3, 3, 11).
python_function('imgl/detect/local.py', '_flood_fill_bbox', 5, 14, 8).
python_function('imgl/detect/local.py', '_detect_panels_simple', 3, 10, 10).
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
python_function('imgl/execute.py', 'execute_action', 1, 13, 12).
python_function('imgl/execute.py', '_display_mismatch_warning', 1, 8, 4).
python_function('imgl/execute.py', '_append_display_warning', 2, 3, 1).
python_function('imgl/execute.py', '_execute_xdotool', 4, 5, 4).
python_function('imgl/execute.py', '_execute_ydotool', 4, 5, 3).
python_function('imgl/execute.py', 'execute_keys', 1, 5, 5).
python_function('imgl/execute.py', '_normalize_keys', 1, 9, 8).
python_function('imgl/export/_escape.py', 'escape_html', 1, 1, 1).
python_function('imgl/export/_escape.py', 'escape_xml', 1, 1, 1).
python_function('imgl/export/actuation_layers.py', 'bbox_center', 1, 10, 3).
python_function('imgl/export/actuation_layers.py', 'bbox_area', 1, 6, 4).
python_function('imgl/export/actuation_layers.py', 'layer_from_bbox', 0, 4, 2).
python_function('imgl/export/actuation_layers.py', '_element_layer_from_dict', 1, 6, 4).
python_function('imgl/export/actuation_layers.py', '_window_layers', 1, 9, 6).
python_function('imgl/export/actuation_layers.py', 'scene_to_actuation_layers', 1, 15, 9).
python_function('imgl/export/actuation_layers.py', 'imgl_result_to_actuation_layers', 1, 3, 3).
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
python_function('imgl/export/vql_adapter.py', '_scene_element_objects', 1, 4, 2).
python_function('imgl/export/vql_adapter.py', 'scene_to_vql', 1, 16, 16).
python_function('imgl/export/vql_adapter.py', 'scene_to_vql_json', 1, 1, 2).
python_function('imgl/export/vql_adapter.py', 'validate_vql_export', 1, 6, 8).
python_function('imgl/export/vql_adapter.py', 'write_vql_program', 2, 4, 10).
python_function('imgl/export/vql_adapter.py', '_grid_layer', 1, 4, 2).
python_function('imgl/export/vql_adapter.py', '_bbox_norm', 3, 5, 2).
python_function('imgl/export/vql_adapter.py', '_location_label', 4, 9, 1).
python_function('imgl/export/vql_adapter.py', '_object_from_bbox', 0, 2, 9).
python_function('imgl/export/vql_adapter.py', '_build_contains_relations', 1, 8, 3).
python_function('imgl/export/vql_adapter.py', '_bbox_contains', 2, 4, 0).
python_function('imgl/export/vql_adapter.py', '_window_to_object', 3, 4, 2).
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
python_function('imgl/installs.py', '_repo_root', 3, 2, 6).
python_function('imgl/installs.py', 'vdisplay_available', 0, 2, 0).
python_function('imgl/installs.py', '_auto_install_vdisplay_enabled', 0, 1, 3).
python_function('imgl/installs.py', 'ensure_vdisplay', 0, 5, 4).
python_function('imgl/installs.py', '_pip_install_editable', 1, 2, 2).
python_function('imgl/installs.py', 'install_img2nl', 0, 2, 3).
python_function('imgl/installs.py', 'install_vdisplay', 0, 2, 3).
python_function('imgl/installs.py', 'install_vql', 0, 1, 3).
python_function('imgl/installs.py', 'install_control', 0, 1, 5).
python_function('imgl/interact.py', '_build_session_catalog', 1, 2, 1).
python_function('imgl/interact.py', 'resolve_imgl_uri', 2, 13, 16).
python_function('imgl/interact.py', '_attach_image_path', 2, 1, 1).
python_function('imgl/interact.py', '_click_by_element_id', 2, 4, 2).
python_function('imgl/interact.py', '_resolve_click', 3, 15, 5).
python_function('imgl/interact.py', '_resolve_type_no_value', 2, 7, 1).
python_function('imgl/interact.py', '_resolve_type_by_element_id', 3, 4, 2).
python_function('imgl/interact.py', '_resolve_type_by_hints', 4, 10, 3).
python_function('imgl/interact.py', '_resolve_type', 3, 14, 7).
python_function('imgl/interact.py', '_annotate_catalog', 1, 6, 7).
python_function('imgl/interact.py', '_select_window', 2, 6, 6).
python_function('imgl/interact.py', '_export_window_previews', 1, 4, 5).
python_function('imgl/interact.py', '_prepare_interactive_session', 1, 4, 12).
python_function('imgl/interact.py', '_show_initial_shell_views', 0, 8, 7).
python_function('imgl/interact.py', '_print_actions_phase_hints', 0, 9, 6).
python_function('imgl/interact.py', '_read_shell_prompt', 2, 4, 4).
python_function('imgl/interact.py', '_handle_resolved_shell_action', 0, 11, 7).
python_function('imgl/interact.py', 'run_interactive_shell', 1, 5, 5).
python_function('imgl/interact.py', '_run_shell_loop', 0, 11, 8).
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
python_function('imgl/nlp2uri.py', 'prompt_to_imgl_uri', 1, 15, 13).
python_function('imgl/nlp2uri.py', '_resolve_click_intent', 2, 3, 5).
python_function('imgl/nlp2uri.py', '_resolve_type_intent', 2, 12, 6).
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
python_function('imgl/pipeline.py', 'analyze', 1, 11, 20).
python_function('imgl/pipeline.py', '_content_metadata', 1, 1, 2).
python_function('imgl/pipeline.py', '_count_roles', 2, 4, 1).
python_function('imgl/preprocess.py', 'load_image', 1, 2, 6).
python_function('imgl/preprocess.py', 'preprocess', 1, 3, 5).
python_function('imgl/scene_cache.py', 'scene_cache_path', 1, 2, 3).
python_function('imgl/scene_cache.py', 'load_cached_scene', 2, 5, 7).
python_function('imgl/scene_cache.py', 'save_scene_cache', 2, 1, 3).
python_function('imgl/scene_cache.py', 'load_or_analyze', 1, 5, 7).
python_function('imgl/targets.py', '_has_chat_token', 1, 1, 3).
python_function('imgl/targets.py', '_bbox_center_x', 1, 5, 3).
python_function('imgl/targets.py', '_bbox_center_y', 1, 5, 3).
python_function('imgl/targets.py', '_parse_layer_fields', 1, 10, 3).
python_function('imgl/targets.py', 'normalize_actuation_element', 1, 7, 3).
python_function('imgl/targets.py', 'normalize_actuation_elements', 1, 3, 2).
python_function('imgl/targets.py', '_target_result', 1, 3, 1).
python_function('imgl/targets.py', '_find_ask_candidate', 1, 12, 7).
python_function('imgl/targets.py', '_find_chat_token_candidate', 1, 5, 4).
python_function('imgl/targets.py', '_find_panel_candidate', 1, 12, 7).
python_function('imgl/targets.py', '_find_input_candidate', 1, 12, 6).
python_function('imgl/targets.py', 'resolve_chat_target', 1, 13, 8).
python_function('imgl/targets.py', '_find_editor_candidate', 1, 13, 6).
python_function('imgl/targets.py', 'resolve_editor_target', 1, 7, 5).
python_function('imgl/targets.py', 'resolve_actuation_target', 1, 2, 2).
python_function('imgl/terminal_md.py', '_c', 2, 1, 1).
python_function('imgl/terminal_md.py', 'stdout_color_enabled', 0, 6, 5).
python_function('imgl/terminal_md.py', '_verdict_color', 1, 1, 3).
python_function('imgl/terminal_md.py', '_highlight_yaml_line', 1, 3, 4).
python_function('imgl/terminal_md.py', '_color_yaml_value', 1, 6, 6).
python_function('imgl/terminal_md.py', '_highlight_bash_line', 1, 10, 9).
python_function('imgl/terminal_md.py', '_highlight_inline', 1, 1, 5).
python_function('imgl/terminal_md.py', '_render_fence_line', 2, 3, 3).
python_function('imgl/terminal_md.py', '_render_normal_line', 1, 6, 9).
python_function('imgl/terminal_md.py', 'colorize_markdown', 1, 11, 12).
python_function('imgl/terminal_md.py', 'print_report', 2, 3, 3).
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
python_function('imgl/vdisplay_bridge.py', '_best_vision_match', 5, 12, 4).
python_function('imgl/vdisplay_bridge.py', 'correlate_windows', 2, 7, 6).
python_function('imgl/vdisplay_bridge.py', '_build_report_recommendations', 0, 10, 5).
python_function('imgl/vdisplay_bridge.py', 'build_window_control_report', 1, 10, 18).
python_function('imgl/vdisplay_context.py', 'from_vdisplay_context', 1, 10, 12).
python_function('imgl/vdisplay_context.py', 'enrich_scene_from_vdisplay', 2, 1, 2).
python_function('imgl/vdisplay_context.py', '_metadata_from_context', 1, 8, 3).
python_function('imgl/vision_ops.py', 'template_available', 0, 2, 0).
python_function('imgl/vision_ops.py', '_png_to_gray_array', 1, 1, 5).
python_function('imgl/vision_ops.py', '_dedupe_matches', 1, 5, 3).
python_function('imgl/vision_ops.py', 'match_template_png', 2, 11, 16).
python_function('imgl/vision_ops.py', 'diff_png_bytes', 2, 11, 8).
python_function('imgl/vision_ops.py', '_crop_png_region', 2, 1, 6).
python_function('imgl/vision_ops.py', '_confidence_color', 1, 5, 0).
python_function('imgl/vision_ops.py', 'render_match_overlay_png', 2, 10, 20).
python_function('imgl/web/__init__.py', 'create_app', 0, 1, 1).
python_function('imgl/web/agent.py', '_catalog_lines', 1, 5, 2).
python_function('imgl/web/agent.py', '_history_lines', 2, 4, 3).
python_function('imgl/web/agent.py', 'pick_agent_action', 3, 10, 13).
python_function('imgl/web/agent.py', '_resolve_act_response', 3, 11, 5).
python_function('imgl/web/agent.py', '_parse_agent_json', 1, 6, 7).
python_function('imgl/web/app.py', 'create_app', 0, 4, 38).
python_function('imgl/web/thumbs.py', '_clamp_box', 1, 3, 2).
python_function('imgl/web/thumbs.py', 'crop_bbox_png', 2, 2, 12).
python_function('imgl/web/thumbs.py', 'window_bbox_dict', 1, 1, 0).
python_function('imgl/window_scope.py', 'is_monolithic_scene', 1, 2, 2).
python_function('imgl/window_scope.py', 'apply_discovered_windows', 1, 1, 3).
python_function('imgl/window_scope.py', 'discover_windows', 1, 2, 3).
python_function('imgl/window_scope.py', 'summarize_windows', 1, 6, 7).
python_function('imgl/window_scope.py', 'pick_focus_window', 1, 11, 5).
python_function('imgl/window_scope.py', 'should_scope_window', 2, 2, 3).
python_function('imgl/window_scope.py', 'scope_to_focus_window', 2, 5, 13).
python_function('imgl/window_scope.py', 'scope_image_to_focus_window', 1, 2, 9).
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
python_function('imgl/window_scope.py', '_score_gutter_candidate', 6, 10, 3).
python_function('imgl/window_scope.py', '_regions_from_balanced_gutters', 3, 10, 10).
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
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_strip_prompt_tokens', 1, 4, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_apply_image_window_flags', 2, 3, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_capture', 2, 5, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_analyze', 2, 5, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_actions', 2, 4, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_resolve', 2, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_click', 2, 3, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_type', 2, 6, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_key', 2, 5, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_execute', 2, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_interaction_verb', 2, 5, 8).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', '_parse_agent', 2, 3, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', 'parse_line', 1, 4, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/grammar.py', 'to_text', 1, 10, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', '_build_interact_session', 0, 4, 10).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', '_run_prompt_act', 1, 8, 7).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_health', 1, 1, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_capture', 1, 5, 11).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_analyze', 1, 4, 6).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_actions', 1, 4, 8).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_resolve', 1, 7, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/handlers/runtime.py', 'handle_execute', 1, 14, 10).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_assign_optional_str', 4, 2, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_assign_execute_flag', 2, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_capture_body', 2, 1, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_analyze_body', 2, 1, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_actions_body', 2, 1, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_resolve_body', 2, 1, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_click_body', 2, 2, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_type_body', 2, 1, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_key_body', 2, 1, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_execute_body', 2, 1, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_agent_body', 2, 2, 4).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_set_body', 2, 2, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_optional_str', 3, 2, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_execute_flag', 2, 2, 0).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_capture_body', 2, 2, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_analyze_body', 2, 3, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_actions_body', 2, 3, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_resolve_body', 2, 1, 1).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_click_body', 2, 2, 3).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_type_body', 2, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_key_body', 2, 2, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_execute_body', 2, 1, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', '_dict_agent_body', 2, 2, 2).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'dict_to_envelope', 1, 1, 5).
python_function('packages/dsl2imgl/src/dsl2imgl/pb_codec.py', 'envelope_to_dict', 1, 4, 5).
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
python_function('packages/dsl2imgl/tests/test_dsl2imgl.py', 'test_capture_analyze_flags', 0, 7, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_schema_registry_covers_all_verbs', 0, 6, 3).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_parse_text_validates_health', 0, 2, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_protobuf_roundtrip_type', 0, 5, 3).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_codec_roundtrip_text', 0, 2, 1).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_dispatch_bytes_envelope', 0, 3, 2).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_event_store_append_command', 1, 4, 4).
python_function('packages/dsl2imgl/tests/test_dsl2imgl_phase4.py', 'test_command_dispatch_records_event_id', 2, 3, 3).
python_function('packages/mcp2imgl/src/mcp2imgl/cli.py', 'main', 1, 2, 5).
python_function('packages/mcp2imgl/src/mcp2imgl/server.py', 'run_stdio', 0, 2, 10).
python_function('packages/nlp2imgl/src/nlp2imgl/cli.py', 'main', 1, 1, 3).
python_function('packages/nlp2imgl/src/nlp2imgl/cli_commands.py', 'output_format', 1, 1, 1).
python_function('packages/nlp2imgl/src/nlp2imgl/cli_commands.py', 'run_to_dsl', 1, 1, 2).
python_function('packages/nlp2imgl/src/nlp2imgl/cli_commands.py', 'run_doctor', 1, 6, 8).
python_function('packages/nlp2imgl/src/nlp2imgl/cli_commands.py', '_print_apply_payload', 2, 3, 5).
python_function('packages/nlp2imgl/src/nlp2imgl/cli_commands.py', 'run_apply', 1, 6, 5).
python_function('packages/nlp2imgl/src/nlp2imgl/cli_parser.py', 'build_parser', 0, 1, 5).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'default_image_path', 0, 3, 4).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'default_window', 0, 3, 2).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', '_result_to_dict', 1, 4, 6).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'doctor_capture', 1, 2, 3).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', '_blocked_capture_response', 0, 1, 1).
python_function('packages/nlp2imgl/src/nlp2imgl/control.py', 'apply_nl_with_diag', 1, 17, 13).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 'use_llm_enabled', 1, 5, 5).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', '_dispatch_dsl_command', 4, 11, 7).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 'to_dsl', 1, 5, 4).
python_function('packages/nlp2imgl/src/nlp2imgl/to_dsl.py', 'apply_nl', 1, 5, 4).
python_function('packages/rest2imgl/src/rest2imgl/app.py', 'create_app', 0, 1, 20).
python_function('packages/rest2imgl/src/rest2imgl/cli.py', 'main', 1, 2, 7).
python_function('packages/uri2imgl/src/uri2imgl/cli.py', 'main', 1, 4, 11).
python_function('packages/uri2imgl/src/uri2imgl/decode.py', '_dsl_click', 2, 4, 1).
python_function('packages/uri2imgl/src/uri2imgl/decode.py', '_dsl_type', 2, 4, 1).
python_function('packages/uri2imgl/src/uri2imgl/decode.py', 'uri_to_dsl', 1, 12, 9).
python_function('tests/conftest.py', '_disable_vdisplay_auto_install', 1, 1, 2).
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
python_function('tests/test_actuation_layers.py', 'test_scene_to_actuation_layers_flattens_window_elements_and_ocr', 0, 8, 4).
python_function('tests/test_actuation_layers.py', 'test_bbox_area_supports_w_h', 0, 2, 1).
python_function('tests/test_actuation_layers.py', 'test_imgl_result_to_actuation_layers_requires_ok', 0, 3, 1).
python_function('tests/test_annotate.py', '_scene', 0, 1, 4).
python_function('tests/test_annotate.py', 'test_default_annotated_path', 0, 2, 2).
python_function('tests/test_annotate.py', 'test_write_annotated_image', 1, 3, 8).
python_function('tests/test_annotate.py', 'test_nlp2uri_mapa', 0, 3, 1).
python_function('tests/test_autodiag.py', 'test_image_freshness_sidecar', 1, 3, 5).
python_function('tests/test_autodiag.py', 'test_verify_capture_updated_fails_on_stale', 1, 1, 4).
python_function('tests/test_autodiag.py', 'test_build_execute_report_json', 0, 3, 2).
python_function('tests/test_autodiag.py', 'test_render_report_markdown_uses_yaml_codeblock', 0, 10, 2).
python_function('tests/test_autodiag.py', 'test_pick_output_format_defaults_to_markdown', 0, 5, 1).
python_function('tests/test_autodiag.py', 'test_build_execute_report_stale_has_current_and_next_cmd', 0, 5, 1).
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
python_function('tests/test_capture_paths.py', 'test_capture_screen_with_mock_vql', 2, 2, 6).
python_function('tests/test_capture_provenance.py', 'test_save_and_load_capture_meta', 1, 3, 3).
python_function('tests/test_capture_provenance.py', 'test_enrich_scene_attaches_capture_meta', 1, 2, 8).
python_function('tests/test_capture_provenance.py', 'test_scene_to_vql_includes_capture_and_relations', 1, 8, 9).
python_function('tests/test_capture_provenance.py', 'test_execute_display_mismatch_warning', 2, 3, 5).
python_function('tests/test_capture_provenance.py', 'test_execute_display_mismatch_strict', 2, 3, 5).
python_function('tests/test_capture_provenance.py', 'test_enrich_scene_correlates_os_windows', 1, 2, 7).
python_function('tests/test_capture_provenance.py', 'test_clear_vql_cache_keeps_capture_meta', 1, 3, 6).
python_function('tests/test_capture_provenance.py', 'test_finalize_capture_enriches_display', 2, 3, 4).
python_function('tests/test_capture_vdisplay.py', 'test_capture_screen_prefers_vdisplay', 1, 3, 7).
python_function('tests/test_capture_vdisplay_priority.py', 'test_capture_prefers_vdisplay_over_portal', 2, 3, 11).
python_function('tests/test_capture_vdisplay_priority.py', 'test_capture_interactive_uses_mirror_not_portal', 1, 2, 6).
python_function('tests/test_capture_vdisplay_priority.py', 'test_capture_interactive_portal_fallback_on_wayland', 2, 3, 6).
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
python_function('tests/test_control_cli.py', 'test_default_image_path_env', 2, 2, 4).
python_function('tests/test_control_cli.py', 'test_default_window_env', 1, 2, 2).
python_function('tests/test_control_cli.py', 'test_run_doctor', 2, 3, 3).
python_function('tests/test_control_cli.py', 'test_run_execute_missing_image', 2, 1, 4).
python_function('tests/test_control_cli.py', 'test_run_execute_loads_openrouter_key_from_dotenv', 2, 3, 9).
python_function('tests/test_control_cli.py', 'test_cli_doctor_help', 0, 4, 2).
python_function('tests/test_control_cli.py', 'test_cli_execute_help', 0, 6, 2).
python_function('tests/test_control_cli.py', 'test_require_nlp2imgl_auto_installs_from_local_packages', 1, 3, 7).
python_function('tests/test_control_cli.py', 'test_cli_default_output_is_markdown', 0, 4, 4).
python_function('tests/test_detect_buttons.py', 'test_valid_button_blob_size_filters_extremes', 0, 5, 1).
python_function('tests/test_detect_buttons.py', 'test_button_role_classifies_icon_vs_button', 0, 3, 1).
python_function('tests/test_detect_buttons.py', 'test_button_confidence_prefers_typical_toolbar_shape', 0, 3, 1).
python_function('tests/test_detect_buttons.py', 'test_overlaps_seen_button_dedupes_high_iou', 0, 3, 1).
python_function('tests/test_detect_buttons.py', 'test_button_from_blob_rect_returns_none_for_invalid_blob', 0, 2, 2).
python_function('tests/test_detect_buttons.py', 'test_detect_buttons_finds_contrast_blob', 0, 5, 5).
python_function('tests/test_detect_buttons.py', 'test_detect_ui_elements_still_includes_buttons', 1, 5, 4).
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
python_function('tests/test_imgl.py', 'test_import', 0, 2, 1).
python_function('tests/test_imgl.py', 'test_bbox_as_xyxy_and_contains', 0, 4, 3).
python_function('tests/test_imgl.py', 'test_scene_roundtrip_json', 0, 8, 8).
python_function('tests/test_imgl.py', 'test_scene_from_dict', 0, 3, 1).
python_function('tests/test_imgl.py', 'test_preprocess_resize', 0, 3, 5).
python_function('tests/test_imgl.py', 'test_analyze_with_mocked_ocr', 1, 10, 8).
python_function('tests/test_imgl.py', 'test_analyze_e2e_with_tesseract', 1, 6, 8).
python_function('tests/test_imgl.py', 'test_cli_analyze_stdout', 2, 4, 9).
python_function('tests/test_imgl.py', 'test_cli_analyze_output_file', 1, 4, 8).
python_function('tests/test_installs.py', 'test_install_img2nl_missing_repo', 2, 1, 4).
python_function('tests/test_installs.py', 'test_install_img2nl_calls_pip', 2, 4, 5).
python_function('tests/test_installs.py', 'test_install_vdisplay_calls_pip', 2, 2, 5).
python_function('tests/test_installs.py', 'test_install_vql_calls_pip', 2, 2, 5).
python_function('tests/test_installs.py', 'test_install_control_calls_pip', 0, 2, 3).
python_function('tests/test_installs.py', 'test_ensure_vdisplay_skips_when_installed', 1, 2, 4).
python_function('tests/test_installs.py', 'test_ensure_vdisplay_auto_installs', 1, 2, 4).
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
python_function('tests/test_nlp2imgl_cli.py', 'test_build_parser_registers_subcommands', 0, 9, 2).
python_function('tests/test_nlp2imgl_cli.py', 'test_run_to_dsl_prints_line', 2, 3, 4).
python_function('tests/test_nlp2imgl_cli.py', 'test_run_apply_uses_json_when_requested', 2, 3, 5).
python_function('tests/test_nlp2imgl_cli.py', 'test_run_doctor_exits_nonzero_on_stale_capture', 1, 2, 3).
python_function('tests/test_nlp2imgl_cli.py', 'test_main_dispatches_apply', 1, 2, 2).
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
python_function('tests/test_targets.py', 'test_resolve_chat_prefers_panel_over_send_chat_ocr_label', 0, 3, 1).
python_function('tests/test_targets.py', 'test_resolve_editor_prefers_window_0', 0, 3, 1).
python_function('tests/test_targets.py', 'test_resolve_chat_picks_bottom_right_input', 0, 2, 1).
python_function('tests/test_terminal_md.py', 'test_stdout_color_disabled_with_no_color', 1, 2, 2).
python_function('tests/test_terminal_md.py', 'test_colorize_markdown_adds_ansi_when_forced', 0, 5, 3).
python_function('tests/test_terminal_md.py', 'test_colorize_markdown_plain_when_disabled', 0, 2, 1).
python_function('tests/test_terminal_md.py', 'test_resolve_cli_output_format_flags', 0, 4, 1).
python_function('tests/test_vdisplay_bridge.py', 'test_suggest_imgl_region_bottom', 0, 2, 1).
python_function('tests/test_vdisplay_bridge.py', 'test_suggest_imgl_region_top', 0, 2, 1).
python_function('tests/test_vdisplay_bridge.py', 'test_correlate_windows_finds_overlap', 0, 4, 2).
python_function('tests/test_vdisplay_bridge.py', 'test_vdisplay_available_is_bool', 0, 2, 2).
python_function('tests/test_vision_ops.py', '_tiny_png', 0, 1, 4).
python_function('tests/test_vision_ops.py', 'test_match_template_png_finds_exact_copy', 0, 3, 3).
python_function('tests/test_vision_ops.py', 'test_diff_png_bytes_detects_change', 0, 3, 6).
python_function('tests/test_vision_ops.py', 'test_render_match_overlay_png', 0, 3, 5).
python_function('tests/test_vision_ops.py', 'test_from_vdisplay_context_metadata_without_image', 0, 4, 1).
python_function('tests/test_vql_export.py', '_sample_scene', 0, 1, 5).
python_function('tests/test_vql_export.py', 'test_scene_to_vql_structure', 0, 20, 4).
python_function('tests/test_vql_export.py', 'test_scene_to_vql_json_roundtrip', 0, 3, 3).
python_function('tests/test_vql_export.py', 'test_write_vql_program', 1, 3, 5).
python_function('tests/test_vql_export.py', 'test_validate_vql_export_when_vql_installed', 0, 2, 5).
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
python_function('tests/test_window_scope.py', 'test_single_monitor_region_bottom_alias', 0, 2, 4).
python_function('tests/test_window_scope.py', 'test_pick_focus_window_prefers_interactive_region', 0, 3, 4).
python_function('tests/test_window_scope.py', 'test_scope_to_focus_window_exports_crop', 1, 5, 8).

% ── Python Classes ───────────────────────────────────────
python_class('imgl/actions.py', 'ActionTarget').
python_method('ActionTarget', 'center', 0, 1, 0).
python_method('ActionTarget', 'click_coords', 0, 1, 1).
python_method('ActionTarget', 'to_click_action', 0, 2, 2).
python_class('imgl/actions.py', 'TypeAction').
python_method('TypeAction', 'coords', 0, 1, 1).
python_method('TypeAction', 'to_dict', 0, 2, 2).
python_class('imgl/actions.py', 'SceneActions').
python_method('SceneActions', 'find', 1, 14, 8).
python_method('SceneActions', '_find_labeled_inputs', 4, 8, 6).
python_method('SceneActions', 'find_one', 1, 2, 1).
python_method('SceneActions', 'click', 1, 2, 4).
python_method('SceneActions', 'type_into', 1, 5, 6).
python_method('SceneActions', 'list_actions', 0, 5, 7).
python_class('imgl/actions.py', 'ElementNotFoundError').
python_class('imgl/capture.py', 'CaptureError').
python_class('imgl/capture.py', 'BlankCaptureError').
python_class('imgl/catalog_types.py', 'InteractiveOption').
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
python_class('imgl/vision_ops.py', 'TemplateMatchResult').
python_method('TemplateMatchResult', 'to_dict', 0, 1, 1).
python_class('imgl/vision_ops.py', 'MatchOverlayItem').
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
python_method('WebSession', '_fail_act', 5, 1, 2).
python_method('WebSession', '_execute_and_recapture', 3, 6, 5).
python_method('WebSession', 'act', 0, 18, 12).
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
makefile_target('IMGL', '').
makefile_target('help', '').
makefile_target('venv', '').
makefile_target('install', '').
makefile_target('install-dev', '').
makefile_target('install-control', '').
makefile_target('install-img2nl', '').
makefile_target('install-vdisplay', '').
makefile_target('install-vql', '').
makefile_target('install-full', '').
makefile_target('capture', '').
makefile_target('capture-interactive', '').
makefile_target('capture-analyze', '').
makefile_target('verify-capture', '').
makefile_target('windows', '').
makefile_target('doctor', '').
makefile_target('doctor-full', '').
makefile_target('execute', '').
makefile_target('execute-dry', '').
makefile_target('execute-llm', '').
makefile_target('shot', '').
makefile_target('test', '').
makefile_target('test-imgl', '').
makefile_target('test-dsl2imgl', '').
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
sumd_interface('web', '').
sumd_workflow('venv', 'manual').
sumd_workflow_step('venv', 1, 'test -x "$(PY)" || $(PYTHON) -m venv "$(VENV)"').
sumd_workflow('install', 'manual').
sumd_workflow_step('install', 1, '$(PIP) install -e .').
sumd_workflow('install-dev', 'manual').
sumd_workflow_step('install-dev', 1, '$(PIP) install -e ".[dev,llm,capture]"').
sumd_workflow_step('install-dev', 2, '$(IMGL) install control').
sumd_workflow_step('install-dev', 3, 'if [ -d "$(VDISPLAY_ROOT)" ]').
sumd_workflow_step('install-dev', 4, '$(PIP) install -e "$(VDISPLAY_ROOT)[pillow]" || $(PIP) install -e "$(VDISPLAY_ROOT)"').
sumd_workflow_step('install-dev', 5, 'fi').
sumd_workflow('install-control', 'manual').
sumd_workflow_step('install-control', 1, '$(IMGL) install control').
sumd_workflow('install-img2nl', 'manual').
sumd_workflow_step('install-img2nl', 1, '$(IMGL) install img2nl').
sumd_workflow('install-vdisplay', 'manual').
sumd_workflow_step('install-vdisplay', 1, '$(IMGL) install vdisplay').
sumd_workflow('install-vql', 'manual').
sumd_workflow_step('install-vql', 1, '$(IMGL) install vql').
sumd_workflow('install-full', 'manual').
sumd_workflow_step('install-full', 1, '$(PIP) install -e ".[web]"').
sumd_workflow('capture', 'manual').
sumd_workflow_step('capture', 1, '$(IMGL) capture --smart -o "$(IMGL_IMAGE)"').
sumd_workflow('capture-interactive', 'manual').
sumd_workflow_step('capture-interactive', 1, 'rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.capture.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)"').
sumd_workflow_step('capture-interactive', 2, 'IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture --portal -o "$(IMGL_IMAGE)" --verify').
sumd_workflow_step('capture-interactive', 3, 'rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)"').
sumd_workflow_step('capture-interactive', 4, 'echo "export IMGL_IMAGE=$(IMGL_IMAGE)"').
sumd_workflow('capture-analyze', 'manual').
sumd_workflow_step('capture-analyze', 1, 'rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.capture.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)"').
sumd_workflow_step('capture-analyze', 2, 'IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture --portal -o "$(IMGL_IMAGE)" --verify --analyze').
sumd_workflow_step('capture-analyze', 3, 'echo "export IMGL_IMAGE=$(IMGL_IMAGE)"').
sumd_workflow('verify-capture', 'manual').
sumd_workflow('windows', 'manual').
sumd_workflow_step('windows', 1, '$(IMGL) map --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('doctor', 'manual').
sumd_workflow_step('doctor', 1, '$(IMGL) doctor --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('doctor-full', 'manual').
sumd_workflow_step('doctor-full', 1, '$(IMGL) doctor --full --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('execute', 'manual').
sumd_workflow_step('execute', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-analyze (lub make capture-interactive)" && exit 1)').
sumd_workflow_step('execute', 2, 'test -n "$(PROMPT)" || (echo "Użycie: make execute PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('execute', 3, '$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('execute-dry', 'manual').
sumd_workflow_step('execute-dry', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-analyze (lub make capture-interactive)" && exit 1)').
sumd_workflow_step('execute-dry', 2, 'test -n "$(PROMPT)" || (echo "Użycie: make execute-dry PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('execute-dry', 3, '$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --dry-run --format "$(FORMAT)"').
sumd_workflow('execute-llm', 'manual').
sumd_workflow_step('execute-llm', 1, 'test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-analyze (lub make capture-interactive)" && exit 1)').
sumd_workflow_step('execute-llm', 2, 'test -n "$(PROMPT)" || (echo "Użycie: make execute-llm PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('execute-llm', 3, 'test -n "$$OPENROUTER_API_KEY" || (echo "Brak OPENROUTER_API_KEY" && exit 1)').
sumd_workflow_step('execute-llm', 4, '$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --llm --format "$(FORMAT)"').
sumd_workflow('shot', 'manual').
sumd_workflow_step('shot', 1, 'test -n "$(PROMPT)" || (echo "Użycie: make shot PROMPT=\'wpisz test w Chat input\'" && exit 1)').
sumd_workflow_step('shot', 2, '$(IMGL) shot "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"').
sumd_workflow('test', 'manual').
sumd_workflow_step('test', 1, '$(PY) -m pytest tests packages/dsl2imgl/tests -q').
sumd_workflow('test-imgl', 'manual').
sumd_workflow_step('test-imgl', 1, '$(PY) -m pytest tests/test_autodiag.py tests/test_vdisplay_bridge.py tests/test_nlp2imgl_control.py tests/test_control_cli.py tests/test_installs.py -q').
sumd_workflow('test-dsl2imgl', 'manual').
sumd_workflow_step('test-dsl2imgl', 1, '$(PY) -m pytest packages/dsl2imgl/tests -q').
sumd_workflow('proto', 'manual').
sumd_workflow_step('proto', 1, 'bash packages/dsl2imgl/scripts/generate-proto.sh').
sumd_workflow('serve-rest', 'manual').
sumd_workflow_step('serve-rest', 1, '$(VENV)/bin/rest2imgl serve --port $(REST_PORT)').
sumd_workflow('serve-web', 'manual').
sumd_workflow_step('serve-web', 1, '$(IMGL) serve --port $(WEB_PORT) --image screen.png --llm --window region-bottom').
sumd_workflow('demo-key', 'manual').
sumd_workflow_step('demo-key', 1, '$(VENV)/bin/dsl2imgl exec \'KEY ctrl+Return EXECUTE 0\'').
sumd_workflow('demo-nl', 'manual').
sumd_workflow_step('demo-nl', 1, 'test -f screen.png || (echo "Brak screen.png — uruchom: imgl capture --interactive -o screen.png" && exit 1)').
sumd_workflow_step('demo-nl', 2, '$(VENV)/bin/nlp2imgl apply "wpisz test w Chat input" --image screen.png --window region-bottom --dry-run').
sumd_workflow('demo-chat', 'manual').
sumd_workflow_step('demo-chat', 1, 'test -f screen.png || (echo "Brak screen.png" && exit 1)').
sumd_workflow_step('demo-chat', 2, '$(VENV)/bin/nlp2imgl apply "wpisz demo w Chat input" --image screen.png --window region-bottom --dry-run').
sumd_workflow_step('demo-chat', 3, '$(VENV)/bin/nlp2imgl apply "naciśnij ctrl+enter" --image screen.png --window region-bottom --dry-run').
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

## Intent

Image to Layout — screenshot OCR and semantic UI reconstruction
