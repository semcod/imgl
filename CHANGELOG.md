# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

