# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.10] - 2026-06-09

### Fixed
- Fix ai-boilerplate issues (ticket-2c58e148)
- Fix string-concat issues (ticket-48321aa5)
- Fix unused-imports issues (ticket-6134672b)
- Fix string-concat issues (ticket-ee86b001)
- Fix unused-imports issues (ticket-4deb65ca)
- Fix magic-numbers issues (ticket-10009555)
- Fix relative-imports issues (ticket-a0a9387a)
- Fix string-concat issues (ticket-13b338b7)
- Fix unused-imports issues (ticket-ede91617)
- Fix magic-numbers issues (ticket-1fe42bad)
- Fix string-concat issues (ticket-af43f13f)
- Fix unused-imports issues (ticket-997b37e6)
- Fix magic-numbers issues (ticket-81a27265)
- Fix string-concat issues (ticket-2f9182d3)
- Fix unused-imports issues (ticket-f86cd724)
- Fix magic-numbers issues (ticket-0b686bc4)
- Fix unused-imports issues (ticket-8a4426f0)
- Fix relative-imports issues (ticket-df74b804)
- Fix unused-imports issues (ticket-0342b906)
- Fix magic-numbers issues (ticket-1dcb1328)
- Fix unused-imports issues (ticket-3237fdc2)
- Fix magic-numbers issues (ticket-8853ee7f)
- Fix ai-boilerplate issues (ticket-a8f90a75)
- Fix unused-imports issues (ticket-bd66e403)
- Fix string-concat issues (ticket-158c8438)
- Fix unused-imports issues (ticket-8b905d5e)
- Fix magic-numbers issues (ticket-c3334bf5)
- Fix string-concat issues (ticket-767a7e1d)
- Fix unused-imports issues (ticket-5d6412ec)
- Fix magic-numbers issues (ticket-07838706)
- Fix unused-imports issues (ticket-b0d49b4e)
- Fix magic-numbers issues (ticket-50720f10)
- Fix relative-imports issues (ticket-06a44d99)
- Fix unused-imports issues (ticket-d08e44bf)
- Fix unused-imports issues (ticket-cf194eb3)
- Fix unused-imports issues (ticket-543fd52e)
- Fix unused-imports issues (ticket-b0d599a1)
- Fix string-concat issues (ticket-9ac2b68b)
- Fix unused-imports issues (ticket-bec34568)
- Fix magic-numbers issues (ticket-c9399ecd)
- Fix string-concat issues (ticket-4d3d663a)
- Fix unused-imports issues (ticket-0e0094d1)
- Fix magic-numbers issues (ticket-6206e954)
- Fix string-concat issues (ticket-f35d8261)
- Fix unused-imports issues (ticket-fecc4bae)
- Fix string-concat issues (ticket-24ee739e)
- Fix unused-imports issues (ticket-c857255e)
- Fix magic-numbers issues (ticket-222c4b85)
- Fix string-concat issues (ticket-22b62ed0)
- Fix unused-imports issues (ticket-330dc368)
- Fix string-concat issues (ticket-c5b5ca3f)
- Fix unused-imports issues (ticket-2d2777ed)
- Fix magic-numbers issues (ticket-2e14353f)
- Fix relative-imports issues (ticket-f38b419b)
- Fix unused-imports issues (ticket-8edfbe43)
- Fix unused-imports issues (ticket-bfa141c7)
- Fix unused-imports issues (ticket-d7505798)
- Fix magic-numbers issues (ticket-d1cee8a9)
- Fix unused-imports issues (ticket-ef90fe9f)
- Fix unused-imports issues (ticket-d380175f)
- Fix string-concat issues (ticket-746cbd46)
- Fix unused-imports issues (ticket-a8708a42)
- Fix string-concat issues (ticket-2cd3d80c)
- Fix unused-imports issues (ticket-440b11bc)
- Fix string-concat issues (ticket-e9eb145e)
- Fix unused-imports issues (ticket-0bb1da60)
- Fix unused-imports issues (ticket-903f24bb)
- Fix magic-numbers issues (ticket-486cdc4a)
- Fix unused-imports issues (ticket-f2619c87)
- Fix magic-numbers issues (ticket-ce989c02)
- Fix smart-return-type issues (ticket-c7374ed6)
- Fix string-concat issues (ticket-8a37d70a)
- Fix unused-imports issues (ticket-bb7b1ab2)
- Fix magic-numbers issues (ticket-42f61592)
- Fix unused-imports issues (ticket-01704e9a)
- Fix magic-numbers issues (ticket-db0f3004)
- Fix string-concat issues (ticket-d7cbf979)
- Fix unused-imports issues (ticket-559ad6e4)
- Fix magic-numbers issues (ticket-48d37d8e)
- Fix unused-imports issues (ticket-0bbc0ffd)
- Fix ai-boilerplate issues (ticket-74b586d3)
- Fix string-concat issues (ticket-40b483da)
- Fix unused-imports issues (ticket-26dc4889)
- Fix magic-numbers issues (ticket-90eae837)
- Fix unused-imports issues (ticket-ec4d57e2)
- Fix magic-numbers issues (ticket-a1e155e1)
- Fix string-concat issues (ticket-514f25c8)
- Fix unused-imports issues (ticket-02ed2d0c)
- Fix magic-numbers issues (ticket-712d72cd)
- Fix unused-imports issues (ticket-04aefa7d)
- Fix unused-imports issues (ticket-45835377)
- Fix ai-boilerplate issues (ticket-6ffce9d6)
- Fix unused-imports issues (ticket-202221be)
- Fix string-concat issues (ticket-c81712cc)
- Fix unused-imports issues (ticket-5606068a)
- Fix string-concat issues (ticket-9324013a)
- Fix unused-imports issues (ticket-ec0f56c5)
- Fix unused-imports issues (ticket-5e28d582)
- Fix magic-numbers issues (ticket-ca548f0d)
- Fix unused-imports issues (ticket-836c881b)

## [Unreleased]

### Added
- `dsl2imgl` Faza 4 — JSON Schema (`schema/commands/`), Protobuf (`proto/dsl2imgl/v1/`), EventStore (`.imgl/events/dsl.events.pb`), CQRS bus
- `packages/*2imgl` — warstwa kontroli: `dsl2imgl`, `uri2imgl`, `nlp2imgl`, `cli2imgl`, `mcp2imgl`, `rest2imgl` (port **8219**)
- Integracja z Koru — `koru/integrations/imgl_client.py`, fallback `KORU_IMGL_FALLBACK`, MCP `koru_imgl_execute`
- `execute` — akcja `key` (Enter, ctrl+Return) przez xdotool
- `docs/` — architektura, control layer, NL shell, głos + przeglądarka, web UI
- `TODO.md` — roadmapa i znane ograniczenia
- `imgl serve` — web UI na porcie 8008: tryb manualny (akcje z miniaturkami) i autonomiczny (agent LLM)
- `examples/workflows/web-ui` — dokumentacja usługi web
- `examples/` — dokumentacja i demo: platformy, workflow, aplikacje, konfiguracje, integracje
- `imgl windows` — wykrywanie regionów, wycinki PNG, podgląd z numerami
- `imgl interact --window` — analiza i LLM per wybrany region
- `window_scope` — detekcja stacked/side-by-side, podział poziomy/pionowy
- `imgl annotate` — PNG overlay with catalog numbers on screenshot
- `imgl interact --annotate --open` — generate and open numbered map
- Shell command / URI `action=annotate` (`mapa`, `obraz`, `numeracja`)
- Vision LLM per-window crop (`--llm` + `--window region-top`)
- LLM catalog merge — pola input z OCR/heurystyki łączone z wynikiem vision LLM

### Fixed
- Action coordinates now map back to full screenshot resolution after OCR downscale
- Default `max_dim=2560` for faster Tesseract on 4K/8K captures
- Scene cache (`layout.imgl.json`) — `uri2vql` list/click/type skips re-OCR when cache matches
- Diagnose vql-fallback returns a short summary instead of empty text

## [0.7.14] - 2026-06-29

### Docs
- Update README.md

### Other
- Update project/planfile-tickets.yaml

## [0.7.13] - 2026-06-25

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.less
- Update imgl/autodiag.py
- Update imgl/capture.py
- Update imgl/classify/gui_heuristics.py
- Update imgl/control.py
- Update imgl/detect/local.py
- Update imgl/export/actuation_layers.py
- Update imgl/export/vql_adapter.py
- Update imgl/interact.py
- Update imgl/targets.py
- ... and 23 more files

## [0.7.12] - 2026-06-24

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Other
- Update app.doql.less
- Update imgl/actions.py
- Update imgl/autodiag.py
- Update imgl/capture.py
- Update imgl/catalog_filter.py
- Update imgl/interact.py
- Update imgl/nlp2uri.py
- Update imgl/terminal_md.py
- Update imgl/window_scope.py
- Update packages/nlp2imgl/src/nlp2imgl/control.py
- ... and 19 more files

## [0.7.11] - 2026-06-24

### Docs
- Update README.md
- Update project/README.md
- Update project/context.md

### Other
- Update imgl/autodiag.py
- Update imgl/cli.py
- Update imgl/targets.py
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- Update project/compact_flow.png
- ... and 10 more files

## [0.7.10] - 2026-06-24

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_actuation_layers.py
- Update tests/test_targets.py
- Update tests/test_vision_ops.py

### Other
- Update VERSION
- Update app.doql.less
- Update imgl/__init__.py
- Update imgl/export/__init__.py
- Update imgl/export/actuation_layers.py
- Update imgl/targets.py
- Update imgl/vdisplay_context.py
- Update imgl/vision_ops.py
- Update layout.vql.imgl.json
- Update project/analysis.toon.yaml
- ... and 18 more files

## [0.7.8] - 2026-06-09

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update project/README.md
- Update project/context.md

### Other
- Update VERSION
- Update app.doql.less
- Update layout.vql.imgl.json
- Update layout.vql.json
- Update project/analysis.toon.yaml
- Update project/calls.mmd
- Update project/calls.png
- Update project/calls.toon.yaml
- Update project/calls.yaml
- Update project/compact_flow.mmd
- ... and 17 more files

## [0.7.7] - 2026-06-09

### Added
- VQL export — `metadata.capture`, `metadata.window_os`, `scene.relations` (`contains`); sidecar `*.capture.json` z vdisplay
- `imgl capture --analyze` / `make capture-analyze` — capture + OCR + VQL w jednym kroku
- `capture_provenance` — korelacja okien imgl z metadanymi OS (vdisplay, IoU); DISPLAY/session_type w sidecarze
- Guard DISPLAY przy `execute` (`IMGL_STRICT_DISPLAY=1` blokuje mismatch względem `.capture.json`)
- `dsl2imgl` — `CAPTURE … ANALYZE [LANG eng+pol]`
- `docs/vql-export.md` — format VQLProgram, pipeline vdisplay → imgl → automatyzacja
- Walidacja eksportu przez `oqlos/vql` (`VQLProgram.validate` + `validate_program_metadata`, schema `program_metadata_imgl.json`)

## [0.7.6] - 2026-06-09

### Docs
- Update README.md

### Other
- Update project/planfile-tickets.yaml
- Update screen.captured_at
- Update screen.png

## [0.7.5] - 2026-06-09

### Docs
- Update README.md

### Other
- Update Makefile
- Update project/planfile-tickets.yaml
- Update screen.captured_at
- Update screen.png

## [0.7.4] - 2026-06-09

### Docs
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/capture.md
- Update project/README.md
- Update project/context.md

### Test
- Update tests/test_capture_vdisplay_priority.py
- Update tests/test_control_cli.py
- Update tests/test_detect_buttons.py
- Update tests/test_nlp2imgl_cli.py

### Other
- Update .gitignore
- Update Makefile
- Update app.doql.less
- Update imgl/capture.py
- Update imgl/catalog.py
- Update imgl/catalog_filter.py
- Update imgl/catalog_heuristic.py
- Update imgl/catalog_types.py
- Update imgl/control.py
- Update imgl/detect/local.py
- ... and 31 more files

## [0.7.3] - 2026-06-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update SUMD.md
- Update SUMR.md
- Update TODO.md
- Update docs/README.md
- Update docs/architecture.md
- Update docs/capture.md
- Update docs/nl-shell-examples.md
- Update docs/web-ui.md
- ... and 9 more files

### Test
- Update testql-scenarios/generated-api-integration.testql.toon.yaml
- Update testql-scenarios/generated-api-smoke.testql.toon.yaml
- Update testql-scenarios/generated-from-pytests.testql.toon.yaml
- Update tests/conftest.py
- Update tests/test_autodiag.py
- Update tests/test_capture_paths.py
- Update tests/test_capture_vdisplay.py
- Update tests/test_capture_vdisplay_priority.py
- Update tests/test_control_cli.py
- Update tests/test_imgl.py
- ... and 6 more files

### Other
- Update .gitignore
- Update Makefile
- Update app.doql.less
- Update examples/img2nl-vql-flow.sh
- Update examples/scripts/demo-agent-loop.sh
- Update imgl/actions.py
- Update imgl/autodiag.py
- Update imgl/capture.py
- Update imgl/cli.py
- Update imgl/control.py
- ... and 37 more files

## [0.7.2] - 2026-06-09

### Docs
- Update CHANGELOG.md
- Update README.md
- Update TODO.md
- Update docs/README.md
- Update docs/architecture.md
- Update docs/control-layer.md
- Update docs/nl-shell-examples.md
- Update docs/voice-browser.md
- Update docs/web-ui.md
- Update examples/README.md
- ... and 18 more files

### Test
- Update tests/test_execute_key.py
- Update tests/test_imgl.py
- Update tests/test_llm_catalog.py
- Update tests/test_nlp2uri_fixes.py
- Update tests/test_web.py
- Update tests/test_window_scope.py

### Other
- Update .gitignore
- Update .imgl/control/layout.vql.imgl.json
- Update .imgl/control/layout.vql.json
- Update Makefile
- Update examples/scripts/demo-agent-loop.sh
- Update examples/scripts/demo-github.sh
- Update examples/scripts/demo-nlp2uri.py
- Update examples/scripts/demo-windows.sh
- Update img.png
- Update imgl/catalog.py
- ... and 78 more files

## [0.7.1] - 2026-06-08

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/test_annotate.py
- Update tests/test_catalog_filter.py
- Update tests/test_catalog_interact.py
- Update tests/test_imgl.py
- Update tests/test_llm_catalog.py
- Update tests/test_scene_cache.py
- Update tests/test_window_scope.py

### Other
- Update .ai/mcp/mcp.json
- Update .idea/pyLspTools.xml
- Update VERSION
- Update imgl/__init__.py
- Update imgl/catalog.py
- Update imgl/catalog_filter.py
- Update imgl/cli.py
- Update imgl/config.py
- Update imgl/coords.py
- Update imgl/diagnose.py
- ... and 22 more files

## [0.7.0] - 2026-06-08

### Added
- `imgl interact` — interactive shell listing windows/buttons/inputs with mouse/keyboard options
- `imgl/catalog.py` — numbered option catalog with positions and action URIs
- `imgl/uri.py` — `vql://window/imgl?action=list|click|type|analyze` DSL builders
- `imgl/nlp2uri.py` — NL → URI (`kliknij Save`, `wpisz tekst w pole`, numer opcji)
- `uri2vql` handlers for `action=list|click|type` on `window/imgl`
- Optional `--execute` via xdotool/ydotool

### Fixed
- OCR `lang=eng+pol` in URI query strings (`+` decoded as space) — normalize to `eng+pol`
- Tesseract fallback to `eng` when compound language pack missing
- `[full]` extra no longer requires unpublished `vql`/`img2vql` from PyPI (fixes `goal -a` / uv)

### Added
- `imgl diagnose` — img2nl check: blank vs meaningful UI content
- `content_check` in scene metadata (`worth_analyzing`, `scene_class`)
- `ImglConfig.check_content`, `skip_blank`, `diagnose_locale`
- Capture warns when img2nl detects empty/low-content screen

### Added (prior)
- `imgl capture` — desktop screenshot to PNG
- `imgl.paths.resolve_image_path()` — clearer missing-file errors

### Fixed
- CLI hints when image path does not exist (suggests `imgl capture`)
- `uri2vql window/imgl` reports file-not-found instead of generic param error

## [0.6.1] - 2026-06-08

### Docs
- Update CHANGELOG.md
- Update README.md

### Test
- Update tests/fixtures/large.png
- Update tests/test_actions.py
- Update tests/test_capture_paths.py
- Update tests/test_diagnose.py
- Update tests/test_export.py
- Update tests/test_imgl.py
- Update tests/test_layout_classify.py
- Update tests/test_ocr_lang.py
- Update tests/test_vql_export.py

### Other
- Update VERSION
- Update imgl/__init__.py
- Update imgl/__main__.py
- Update imgl/actions.py
- Update imgl/capture.py
- Update imgl/classify/__init__.py
- Update imgl/classify/gui_heuristics.py
- Update imgl/cli.py
- Update imgl/config.py
- Update imgl/core.py
- ... and 25 more files

## [0.6.0] - 2026-06-08

### Added
- `imgl/actions.py` — `SceneActions` with `find`, `click`, `type_into`, `list_actions`
- `ActionTarget`, `TypeAction`, `ElementNotFoundError`
- CLI: `imgl find` with `--click`, `--type-into`, `--list`

## [0.5.0] - 2026-06-08

### Added
- `scene_to_vql()`, `scene_to_vql_json()`, `write_vql_program()` — VQL program export
- CLI: `imgl vql` with `--with-grid` / `--grid`
- `uri2vql` handler: `vql://window/imgl?image=...&file=...`

## [0.4.0] - 2026-06-08

### Added
- `scene_to_html()` — absolutely positioned HTML with semantic tags and `data-*` selectors
- `scene_to_svg()` — wireframe and overlay SVG export modes
- CLI commands: `imgl html`, `imgl svg`

## [0.3.0] - 2026-06-08

### Added
- Local UI detection: titlebar, panels, windows, buttons (`imgl.detect.local`)
- Optional `img2vql` bridge when package is installed
- Input frame detection (`imgl.detect.rectangles`)
- Layout module: window building, OCR assignment, title extraction
- GUI heuristics: classify `button`, `input`, `label`, `text`, `toolbar`
- Geometry helpers (`iou`, `center_in`)

### Changed
- `analyze()` now returns classified elements per window instead of raw OCR text only

## [0.2.0] - 2026-06-08

### Added
- Core types: `Scene`, `Window`, `Element`, `BBox`, `OcrBox`
- OCR pipeline with Tesseract backend (`pytesseract`)
- `analyze()` API and JSON export (`scene_to_json`)
- CLI: `imgl analyze <image> --json`
- Image preprocessing with optional downscaling

### Changed
- Repurposed package from image generation stub to screenshot layout analysis

### Removed
- `ImageGenerator` stub (`imgl.core`)

## [0.1.1] - 2026-06-08

### Docs
- Update README.md

### Test
- Update tests/test_imgl.py

### Other
- Update .env.example
- Update .idea/.gitignore
- Update .idea/imgl.iml
- Update .idea/inspectionProfiles/Project_Default.xml
- Update .idea/inspectionProfiles/profiles_settings.xml
- Update .idea/modules.xml
- Update .idea/vcs.xml
- Update imgl/__init__.py
- Update imgl/__main__.py
- Update imgl/core.py
- ... and 1 more files

