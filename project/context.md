# System Architecture Analysis
<!-- generated in 0.00s -->

## Overview

- **Project**: /home/tom/github/semcod/imgl
- **Primary Language**: python
- **Languages**: python: 84, json: 14, yaml: 7, shell: 7, toml: 7
- **Analysis Mode**: static
- **Total Functions**: 503
- **Total Classes**: 38
- **Modules**: 122
- **Entry Points**: 120

## Architecture by Module

### packages.dsl2imgl.src.dsl2imgl.pb_codec
- **Functions**: 32
- **File**: `pb_codec.py`

### imgl.window_scope
- **Functions**: 29
- **Classes**: 1
- **File**: `window_scope.py`

### imgl.capture
- **Functions**: 28
- **Classes**: 2
- **File**: `capture.py`

### imgl.autodiag
- **Functions**: 27
- **File**: `autodiag.py`

### imgl.detect.local
- **Functions**: 20
- **Classes**: 1
- **File**: `local.py`

### imgl.web.session
- **Functions**: 18
- **Classes**: 5
- **File**: `session.py`

### imgl.interact
- **Functions**: 17
- **Classes**: 1
- **File**: `interact.py`

### imgl.actions
- **Functions**: 16
- **Classes**: 4
- **File**: `actions.py`

### imgl.llm_catalog
- **Functions**: 16
- **File**: `llm_catalog.py`

### imgl.control
- **Functions**: 16
- **File**: `control.py`

### packages.dsl2imgl.src.dsl2imgl.grammar
- **Functions**: 16
- **File**: `grammar.py`

### imgl.export.annotate_export
- **Functions**: 14
- **File**: `annotate_export.py`

### imgl.export.vql_adapter
- **Functions**: 13
- **File**: `vql_adapter.py`

### imgl.vdisplay_bridge
- **Functions**: 12
- **File**: `vdisplay_bridge.py`

### imgl.types
- **Functions**: 10
- **Classes**: 5
- **File**: `types.py`

### imgl.diagnose
- **Functions**: 10
- **Classes**: 1
- **File**: `diagnose.py`

### imgl.freshness
- **Functions**: 9
- **File**: `freshness.py`

### imgl.terminal_md
- **Functions**: 9
- **File**: `terminal_md.py`

### imgl.installs
- **Functions**: 9
- **File**: `installs.py`

### imgl.classify.gui_heuristics
- **Functions**: 9
- **File**: `gui_heuristics.py`

## Key Entry Points

Main execution flows into the system:

### imgl.cli.main
- **Calls**: imgl.cli.build_parser, parser.parse_args, ImglConfig, packages.nlp2imgl.src.nlp2imgl.cli_commands.run_doctor, imgl.terminal_md.print_report, imgl.control.run_map, imgl.terminal_md.print_report, imgl.terminal_md.print_report

### imgl.web.app.create_app
- **Calls**: None.resolve, SessionManager.create, FastAPI, static_dir.is_dir, app.get, app.get, app.get, app.get

### packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_execute
- **Calls**: None.upper, cmd.get, packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session, packages.dsl2imgl.src.dsl2imgl.handlers.runtime._run_prompt_act, DslResult, str, imgl.execute.execute_action, DslResult

### imgl.web.session.WebSession.act
- **Calls**: self._step_record, self.history.append, self.resolve_index, self._step_record, self.history.append, result.get, self._step_record, self.history.append

### imgl.types.Scene.from_dict
- **Calls**: data.get, cls, BBox, Element, Window, element_from_dict, OcrBox, data.get

### packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb
- **Calls**: result_pb2.DslEvent, pb.command.CopyFrom, DslResult, pb.result.CopyFrom, pb.SerializeToString, packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope, packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb, self.path.with_suffix

### packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl
- **Calls**: event.to_dict, result_pb2.DslEvent, pb_event.command.CopyFrom, DslResult, pb_event.result.CopyFrom, None.decode, self.path.open, fh.write

### examples.scripts.demo-nlp2uri.main
- **Calls**: print, imgl.pipeline.analyze, imgl.window_scope.apply_discovered_windows, imgl.catalog.build_interactive_catalog, InteractSession, print, print, imgl.nlp2uri.prompt_to_imgl_uri

### packages.dsl2imgl.src.dsl2imgl.cli.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, exec_p.add_argument, sub.add_parser, argparse.ArgumentParser, legacy.add_argument, legacy.add_argument

### packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_capture
- **Calls**: bool, bool, cmd.get, cmd.get, cmd.get, cmd.get, imgl.capture.capture_screen, DslResult

### imgl.actions.SceneActions.find
> Find elements matching type, text, label, or window.
- **Calls**: imgl.actions._iter_elements, targets.append, imgl.actions._iter_elements, ActionTarget, any, imgl.actions._find_label_for_input, _infer_input_label, imgl.actions._text_matches

### imgl.ocr.tesseract.TesseractOcr.run
- **Calls**: imgl.ocr.lang.ocr_lang_attempts, len, range, ImportError, RuntimeError, None.strip, int, int

### imgl.web.session.SessionManager.create
- **Calls**: None.resolve, work.mkdir, WebSession, None.is_file, cls, None.resolve, img.is_file, session.analyze

### packages.uri2imgl.src.uri2imgl.cli.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, dec.add_argument, sub.add_parser, run.add_argument, run.add_argument, parser.parse_args

### packages.cli2imgl.src.cli2imgl.cli.main
- **Calls**: print, print, None.strip, packages.dsl2imgl.src.dsl2imgl.bus.dispatch, print, packages.nlp2imgl.src.nlp2imgl.to_dsl.apply_nl, json.dumps, print

### packages.dsl2imgl.src.dsl2imgl.events.EventStore.replay
- **Calls**: None.splitlines, self.replay_pb, self.path.is_file, json.loads, events.append, self.path.read_text, line.strip, StoredEvent

### packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_resolve
- **Calls**: cmd.get, DslResult, packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session, packages.dsl2imgl.src.dsl2imgl.handlers.runtime._run_prompt_act, DslResult, outcome.get, DslResult, outcome.get

### packages.dsl2imgl.src.dsl2imgl.events.EventStore.replay_pb
- **Calls**: pb_path.read_bytes, self.path.with_suffix, pb_path.is_file, len, int.from_bytes, result_pb2.DslEvent, pb.ParseFromString, events.append

### imgl.window_scope.scope_image_to_focus_window
> Analyze screenshot, pick focus window, export crop PNG.
- **Calls**: ImglConfig, imgl.pipeline.analyze, imgl.window_scope.apply_discovered_windows, imgl.window_scope.scope_to_focus_window, str, str, len, str

### imgl.control.run_doctor
- **Calls**: imgl.autodiag.render_report, str, str, imgl.control.default_window, imgl.vdisplay_bridge.build_window_control_report, imgl.autodiag.diagnose_capture, capture.get, imgl.control.default_image_path

### packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_actions
- **Calls**: cmd.get, packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session, DslResult, opt.to_dict, DslResult, cmd.get, bool, json.dumps

### imgl.capture._capture_with_gnome_shell
> GNOME Shell D-Bus screenshot (works on Mutter; grim needs wlroots).
- **Calls**: path.parent.mkdir, path.is_file, None.strip, shutil.which, path.unlink, subprocess.run, path.is_file, detail.lower

### packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_analyze
- **Calls**: cmd.get, packages.dsl2imgl.src.dsl2imgl.handlers.runtime._build_interact_session, DslResult, DslResult, cmd.get, bool, cmd.get, len

### imgl.actions.SceneActions.list_actions
> List available click/type actions for interactive elements.
- **Calls**: imgl.actions._iter_elements, actions.append, None.to_click_action, actions.append, None.to_dict, ActionTarget, TypeAction, ActionTarget

### packages.rest2imgl.src.rest2imgl.cli.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, serve.add_argument, serve.add_argument, parser.parse_args, uvicorn.run, packages.rest2imgl.src.rest2imgl.app.create_app

### packages.nlp2imgl.src.nlp2imgl.cli_commands.run_apply
- **Calls**: packages.nlp2imgl.src.nlp2imgl.control.apply_nl_with_diag, packages.nlp2imgl.src.nlp2imgl.cli_commands._print_apply_payload, packages.nlp2imgl.src.nlp2imgl.cli_commands.output_format, None.get, bool, payload.get, checks.get, payload.get

### packages.dsl2imgl.src.dsl2imgl.grammar._parse_interaction_verb
- **Calls**: None.upper, packages.dsl2imgl.src.dsl2imgl.grammar._apply_image_window_flags, packages.dsl2imgl.src.dsl2imgl.grammar._parse_click, packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag, str, packages.dsl2imgl.src.dsl2imgl.grammar._parse_type, packages.dsl2imgl.src.dsl2imgl.grammar._parse_key, packages.dsl2imgl.src.dsl2imgl.grammar._parse_execute

### imgl.capture._capture_with_grim
- **Calls**: path.parent.mkdir, None.strip, shutil.which, subprocess.run, path.is_file, str, str, path.stat

### packages.dsl2imgl.src.dsl2imgl.events.EventStore.append_command
- **Calls**: StoredEvent, self.path.parent.mkdir, uuid.uuid4, self._append_pb, self._append_jsonl, int, time.time

### imgl.actions.SceneActions.type_into
> Resolve a type action for an input field.
- **Calls**: self.find_one, None.to_dict, self.find_one, ElementNotFoundError, target.element.metadata.get, imgl.actions._format_query, TypeAction

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [imgl.cli]
  └─> build_parser
      └─> _add_common_args
  └─ →> run_doctor
      └─> output_format
          └─ →> resolve_cli_output_format
      └─ →> build_window_control_report
  └─ →> print_report
      └─> colorize_markdown
          └─> stdout_color_enabled
```

### Flow 2: create_app
```
create_app [imgl.web.app]
```

### Flow 3: handle_execute
```
handle_execute [packages.dsl2imgl.src.dsl2imgl.handlers.runtime]
  └─> _build_interact_session
      └─ →> load_or_analyze
          └─> save_scene_cache
          └─> load_cached_scene
  └─> _run_prompt_act
      └─ →> prompt_to_imgl_uri
      └─ →> resolve_imgl_uri
          └─ →> actions
```

### Flow 4: act
```
act [imgl.web.session.WebSession]
```

### Flow 5: from_dict
```
from_dict [imgl.types.Scene]
```

### Flow 6: _append_pb
```
_append_pb [packages.dsl2imgl.src.dsl2imgl.events.EventStore]
```

### Flow 7: _append_jsonl
```
_append_jsonl [packages.dsl2imgl.src.dsl2imgl.events.EventStore]
```

### Flow 8: handle_capture
```
handle_capture [packages.dsl2imgl.src.dsl2imgl.handlers.runtime]
```

### Flow 9: find
```
find [imgl.actions.SceneActions]
  └─ →> _iter_elements
      └─> _window_matches
      └─ →> get_discovered_window
          └─> discover_windows
  └─ →> _iter_elements
      └─> _window_matches
      └─ →> get_discovered_window
          └─> discover_windows
```

### Flow 10: run
```
run [imgl.ocr.tesseract.TesseractOcr]
  └─ →> ocr_lang_attempts
      └─> normalize_ocr_lang
```

## Key Classes

### imgl.web.session.WebSession
- **Methods**: 12
- **Key Methods**: imgl.web.session.WebSession.__post_init__, imgl.web.session.WebSession.refresh_catalog, imgl.web.session.WebSession.analyze, imgl.web.session.WebSession.capture, imgl.web.session.WebSession.select_window, imgl.web.session.WebSession.resolve_prompt, imgl.web.session.WebSession.resolve_index, imgl.web.session.WebSession.act, imgl.web.session.WebSession.state_dict, imgl.web.session.WebSession._refresh_annotated_png

### packages.dsl2imgl.src.dsl2imgl.events.EventStore
- **Methods**: 7
- **Key Methods**: packages.dsl2imgl.src.dsl2imgl.events.EventStore.__init__, packages.dsl2imgl.src.dsl2imgl.events.EventStore.for_default, packages.dsl2imgl.src.dsl2imgl.events.EventStore.append_command, packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_pb, packages.dsl2imgl.src.dsl2imgl.events.EventStore._append_jsonl, packages.dsl2imgl.src.dsl2imgl.events.EventStore.replay_pb, packages.dsl2imgl.src.dsl2imgl.events.EventStore.replay

### imgl.actions.SceneActions
> Find and interact with elements in a Scene.
- **Methods**: 5
- **Key Methods**: imgl.actions.SceneActions.find, imgl.actions.SceneActions.find_one, imgl.actions.SceneActions.click, imgl.actions.SceneActions.type_into, imgl.actions.SceneActions.list_actions

### imgl.types.BBox
- **Methods**: 4
- **Key Methods**: imgl.types.BBox.as_xyxy, imgl.types.BBox.contains, imgl.types.BBox.to_dict, imgl.types.BBox.from_xyxy

### imgl.actions.ActionTarget
> A resolved UI element that can be clicked or typed into.
- **Methods**: 3
- **Key Methods**: imgl.actions.ActionTarget.center, imgl.actions.ActionTarget.click_coords, imgl.actions.ActionTarget.to_click_action

### imgl.web.session.SessionManager
> Single global session for local desktop control.
- **Methods**: 3
- **Key Methods**: imgl.web.session.SessionManager.__init__, imgl.web.session.SessionManager.create, imgl.web.session.SessionManager.auto_select_first_window

### packages.dsl2imgl.src.dsl2imgl.result.DslResult
- **Methods**: 2
- **Key Methods**: packages.dsl2imgl.src.dsl2imgl.result.DslResult.to_dict, packages.dsl2imgl.src.dsl2imgl.result.DslResult.to_json

### imgl.actions.TypeAction
> Type text into an input field.
- **Methods**: 2
- **Key Methods**: imgl.actions.TypeAction.coords, imgl.actions.TypeAction.to_dict

### imgl.window_scope.WindowSummary
> One discoverable window region with stats for the picker UI.
- **Methods**: 2
- **Key Methods**: imgl.window_scope.WindowSummary.label, imgl.window_scope.WindowSummary.bbox

### imgl.types.Scene
- **Methods**: 2
- **Key Methods**: imgl.types.Scene.to_dict, imgl.types.Scene.from_dict

### packages.dsl2imgl.src.dsl2imgl.events.StoredEvent
- **Methods**: 1
- **Key Methods**: packages.dsl2imgl.src.dsl2imgl.events.StoredEvent.to_dict

### imgl.nlp2uri.ResolvedImglUri
- **Methods**: 1
- **Key Methods**: imgl.nlp2uri.ResolvedImglUri.to_dict

### imgl.types.OcrBox
- **Methods**: 1
- **Key Methods**: imgl.types.OcrBox.to_dict

### imgl.types.Element
- **Methods**: 1
- **Key Methods**: imgl.types.Element.to_dict

### imgl.types.Window
- **Methods**: 1
- **Key Methods**: imgl.types.Window.to_dict

### imgl.catalog_types.InteractiveOption
> One selectable UI target with mouse/keyboard affordances.
- **Methods**: 1
- **Key Methods**: imgl.catalog_types.InteractiveOption.to_dict

### imgl.ocr.base.OcrBackend
- **Methods**: 1
- **Key Methods**: imgl.ocr.base.OcrBackend.run
- **Inherits**: Protocol

### imgl.ocr.tesseract.TesseractOcr
> Extract word-level bounding boxes using pytesseract.
- **Methods**: 1
- **Key Methods**: imgl.ocr.tesseract.TesseractOcr.run

### imgl.web.session.StepRecord
- **Methods**: 1
- **Key Methods**: imgl.web.session.StepRecord.to_dict

### imgl.web.session.AgentState
- **Methods**: 1
- **Key Methods**: imgl.web.session.AgentState.to_dict

## Data Transformation Functions

Key functions that process and transform data:

### packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf
- **Output to**: None.SerializeToString, packages.dsl2imgl.src.dsl2imgl.pb_codec.dict_to_envelope

### packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf
- **Output to**: command_pb2.DslEnvelope, envelope.ParseFromString, packages.dsl2imgl.src.dsl2imgl.pb_codec.envelope_to_dict

### packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_text_to_protobuf
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar.parse_line, packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_protobuf, ValueError

### packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf_to_text
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar.to_text, packages.dsl2imgl.src.dsl2imgl.pb_codec.decode_protobuf

### packages.dsl2imgl.src.dsl2imgl.pb_codec.encode_result_protobuf
- **Output to**: None.SerializeToString, packages.dsl2imgl.src.dsl2imgl.pb_codec.result_to_pb

### packages.dsl2imgl.src.dsl2imgl.schema_registry.validate_schemas
- **Output to**: None.items, None.get, packages.dsl2imgl.src.dsl2imgl.schema_registry._load_schemas, errors.append, None.get

### packages.dsl2imgl.src.dsl2imgl.codec.validate_payload
- **Output to**: None.upper, packages.dsl2imgl.src.dsl2imgl.schema_registry.schema_for_verb, jsonschema.validate, ValueError, str

### packages.dsl2imgl.src.dsl2imgl.codec.parse_text
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar.parse_line, packages.dsl2imgl.src.dsl2imgl.codec.validate_payload

### packages.nlp2imgl.src.nlp2imgl.cli_parser.build_parser
- **Output to**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, to_dsl_p.add_argument, to_dsl_p.add_argument

### packages.nlp2imgl.src.nlp2imgl.cli_commands.output_format
- **Output to**: imgl.autodiag.resolve_cli_output_format

### imgl.autodiag.resolve_cli_output_format
> CLI default is markdown; --json / --yaml select structured output.
- **Output to**: ValueError

### imgl.autodiag.pick_output_format

### imgl.autodiag._parse_coords
- **Output to**: _COORD_RE.search, int, int, match.group, match.group

### imgl.autodiag._parse_typed_text
- **Output to**: _TYPED_RE.search, match.group

### imgl.autodiag._parse_keys
- **Output to**: _KEY_RE.search, None.strip, match.group

### imgl.actions._format_query
- **Output to**: parts.append, parts.append, parts.append, parts.append, None.join

### imgl.catalog.format_catalog_table
> Human-readable numbered list for the interactive shell.
- **Output to**: lines.append, lines.append, lines.append, None.join, lines.append

### imgl.preprocess.preprocess
> Load and optionally downscale an image for analysis.
- **Output to**: imgl.preprocess.load_image, max, PreprocessedImage, max, max

### imgl.llm_catalog._parse_json_payload
- **Output to**: json.loads, re.search, json.loads, match.group

### imgl.window_scope.format_window_picker
- **Output to**: lines.extend, None.join, lines.append, lines.append, len

### imgl.web.agent._parse_agent_json
- **Output to**: raw.strip, re.search, fence.group, text.find, text.rfind

### packages.dsl2imgl.src.dsl2imgl.grammar._parse_capture
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag, packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag, packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag

### packages.dsl2imgl.src.dsl2imgl.grammar._parse_analyze
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag, packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag

### packages.dsl2imgl.src.dsl2imgl.grammar._parse_actions
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar.pick_flag

### packages.dsl2imgl.src.dsl2imgl.grammar._parse_resolve
- **Output to**: packages.dsl2imgl.src.dsl2imgl.grammar._strip_prompt_tokens, packages.dsl2imgl.src.dsl2imgl.grammar._apply_image_window_flags

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `imgl.cli.main` - 131 calls
- `imgl.cli.build_parser` - 116 calls
- `imgl.web.app.create_app` - 107 calls
- `imgl.control.smart_capture` - 42 calls
- `imgl.autodiag.diagnose_capture` - 41 calls
- `imgl.terminal_md.colorize_markdown` - 40 calls
- `imgl.nlp2uri.prompt_to_imgl_uri` - 37 calls
- `packages.rest2imgl.src.rest2imgl.app.create_app` - 36 calls
- `packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_execute` - 35 calls
- `imgl.web.session.WebSession.act` - 34 calls
- `imgl.autodiag.build_operation_step` - 33 calls
- `imgl.capture.capture_screen` - 33 calls
- `imgl.export.vql_adapter.scene_to_vql` - 33 calls
- `imgl.vdisplay_bridge.correlate_windows` - 32 calls
- `imgl.vdisplay_bridge.build_window_control_report` - 32 calls
- `imgl.coords.scale_scene_to_screen` - 29 calls
- `imgl.classify.gui_heuristics.classify_scene_elements` - 29 calls
- `imgl.types.Scene.from_dict` - 28 calls
- `imgl.control.capture_interactive` - 28 calls
- `imgl.execute.execute_action` - 27 calls
- `examples.scripts.demo-nlp2uri.main` - 25 calls
- `imgl.control.run_execute` - 25 calls
- `imgl.export.annotate_export.scene_to_annotated_image` - 25 calls
- `packages.nlp2imgl.src.nlp2imgl.cli_parser.build_parser` - 24 calls
- `imgl.web.agent.pick_agent_action` - 23 calls
- `packages.dsl2imgl.src.dsl2imgl.cli.main` - 22 calls
- `imgl.pipeline.analyze` - 22 calls
- `imgl.detect.rectangles.detect_input_frames` - 22 calls
- `packages.dsl2imgl.src.dsl2imgl.bus.dispatch` - 21 calls
- `imgl.freshness.image_freshness` - 21 calls
- `packages.dsl2imgl.src.dsl2imgl.handlers.runtime.handle_capture` - 21 calls
- `imgl.export.annotate_export.write_window_preview_images` - 20 calls
- `packages.dsl2imgl.src.dsl2imgl.grammar.to_text` - 20 calls
- `packages.nlp2imgl.src.nlp2imgl.to_dsl.to_dsl` - 19 calls
- `imgl.interact.resolve_imgl_uri` - 19 calls
- `imgl.actions.SceneActions.find` - 18 calls
- `imgl.autodiag.build_execute_report` - 17 calls
- `imgl.ocr.tesseract.TesseractOcr.run` - 17 calls
- `imgl.web.session.SessionManager.create` - 17 calls
- `imgl.interact.run_interactive_shell` - 17 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> build_parser
    main --> parse_args
    main --> ImglConfig
    main --> run_doctor
    main --> print_report
    create_app --> resolve
    create_app --> create
    create_app --> FastAPI
    create_app --> is_dir
    create_app --> get
    handle_execute --> upper
    handle_execute --> get
    handle_execute --> _build_interact_sess
    handle_execute --> _run_prompt_act
    handle_execute --> DslResult
    act --> _step_record
    act --> append
    act --> resolve_index
    from_dict --> get
    from_dict --> cls
    from_dict --> BBox
    from_dict --> Element
    from_dict --> Window
    _append_pb --> DslEvent
    _append_pb --> CopyFrom
    _append_pb --> DslResult
    _append_pb --> SerializeToString
    _append_jsonl --> to_dict
    _append_jsonl --> DslEvent
    _append_jsonl --> CopyFrom
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.