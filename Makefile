SHELL := /usr/bin/env bash

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python
IMGL := $(VENV)/bin/imgl

REST_PORT ?= 8219
WEB_PORT ?= 8008
VDISPLAY_ROOT ?= $(HOME)/github/wronai/vdisplay
IMGL_IMAGE ?= screen.png
IMGL_WINDOW ?= region-bottom
FORMAT ?= markdown
PROMPT ?=

.PHONY: help venv install install-dev install-control install-full install-img2nl install-vdisplay install-vql
.PHONY: capture capture-interactive verify-capture windows doctor doctor-full execute execute-dry execute-llm shot
.PHONY: test test-imgl test-dsl2imgl proto serve-rest serve-web demo-key demo-nl demo-chat

help:
	@echo "imgl — Makefile (instalacja + aliasy → komendy imgl)"
	@echo ""
	@echo "Instalacja:"
	@echo "  make install-dev         pip install -e '.[dev,llm,capture]'"
	@echo "  make install-control     imgl install control"
	@echo "  make install-img2nl      imgl install img2nl"
	@echo "  make install-vdisplay    imgl install vdisplay"
	@echo "  make install-vql         imgl install vql"
	@echo "  make install-full        + web"
	@echo ""
	@echo "Workflow:"
	@echo "  make capture-interactive   portal GNOME → $(IMGL_IMAGE) (Wayland; wybierz region)"
	@echo "  make doctor-full           autodiagnostyka (markdown)"
	@echo "  make execute-llm PROMPT='wpisz test w Chat input'"
	@echo "  make shot PROMPT='wpisz test w Chat input'"
	@echo ""
	@echo "Testy:"
	@echo "  make test | make test-imgl"
	@echo ""
	@echo "Usługi:"
	@echo "  make serve-rest | make serve-web"

venv:
	@test -x "$(PY)" || $(PYTHON) -m venv "$(VENV)"

install: venv
	$(PIP) install -e .

install-dev: install
	$(PIP) install -e ".[dev,llm,capture]"
	$(IMGL) install control
	@if [ -d "$(VDISPLAY_ROOT)" ]; then \
		$(PIP) install -e "$(VDISPLAY_ROOT)[pillow]" || $(PIP) install -e "$(VDISPLAY_ROOT)"; \
	fi

install-control: install-dev
	$(IMGL) install control

install-img2nl: install-dev
	$(IMGL) install img2nl

install-vdisplay: install-dev
	$(IMGL) install vdisplay

install-vql: install-dev
	$(IMGL) install vql

install-full: install-control
	$(PIP) install -e ".[web]"

capture: install-dev
	$(IMGL) capture --smart -o "$(IMGL_IMAGE)"

capture-interactive: install-dev
	rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)" "$(IMGL_IMAGE:.png=.captured_at)" "$(IMGL_IMAGE)"
	IMGL_CAPTURE_PORTAL_FALLBACK=1 $(IMGL) capture --portal -o "$(IMGL_IMAGE)" --verify
	rm -f "$(IMGL_IMAGE:.png=.vql.imgl.json)" "$(IMGL_IMAGE:.png=.vql.json)"
	@echo "export IMGL_IMAGE=$(IMGL_IMAGE)"

verify-capture: install-dev
	@BEFORE=$${BEFORE:-$$(stat -c %Y "$(IMGL_IMAGE)" 2>/dev/null || echo 0)}; \
	$(IMGL) verify "$(IMGL_IMAGE)" --before "$$BEFORE"

windows: install-dev
	$(IMGL) map --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"

doctor: install-dev
	$(IMGL) doctor --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"

doctor-full: install-dev
	$(IMGL) doctor --full --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"

execute: install-control
	@test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1)
	@test -n "$(PROMPT)" || (echo "Użycie: make execute PROMPT='wpisz test w Chat input'" && exit 1)
	$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"

execute-dry: install-control
	@test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1)
	@test -n "$(PROMPT)" || (echo "Użycie: make execute-dry PROMPT='wpisz test w Chat input'" && exit 1)
	$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --dry-run --format "$(FORMAT)"

execute-llm: install-control
	@test -f "$(IMGL_IMAGE)" || (echo "Brak zrzutu — najpierw: make capture-interactive" && exit 1)
	@test -n "$(PROMPT)" || (echo "Użycie: make execute-llm PROMPT='wpisz test w Chat input'" && exit 1)
	@test -n "$$OPENROUTER_API_KEY" || (echo "Brak OPENROUTER_API_KEY" && exit 1)
	$(IMGL) execute "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --llm --format "$(FORMAT)"

shot: install-control
	@test -n "$(PROMPT)" || (echo "Użycie: make shot PROMPT='wpisz test w Chat input'" && exit 1)
	$(IMGL) shot "$(PROMPT)" --image "$(IMGL_IMAGE)" --window "$(IMGL_WINDOW)" --format "$(FORMAT)"

test:
	$(PY) -m pytest tests packages/dsl2imgl/tests -q

test-imgl:
	$(PY) -m pytest tests/test_autodiag.py tests/test_vdisplay_bridge.py tests/test_nlp2imgl_control.py tests/test_control_cli.py tests/test_installs.py -q

test-dsl2imgl:
	$(PY) -m pytest packages/dsl2imgl/tests -q

proto:
	bash packages/dsl2imgl/scripts/generate-proto.sh

serve-rest: install-control
	$(VENV)/bin/rest2imgl serve --port $(REST_PORT)

serve-web: install-full
	$(IMGL) serve --port $(WEB_PORT) --image screen.png --llm --window region-bottom

demo-key: install-control
	$(VENV)/bin/dsl2imgl exec 'KEY ctrl+Return EXECUTE 0'

demo-nl: install-control
	@test -f screen.png || (echo "Brak screen.png — uruchom: imgl capture --interactive -o screen.png" && exit 1)
	$(VENV)/bin/nlp2imgl apply "wpisz test w Chat input" --image screen.png --window region-bottom --dry-run

demo-chat: install-control
	@test -f screen.png || (echo "Brak screen.png" && exit 1)
	$(VENV)/bin/nlp2imgl apply "wpisz demo w Chat input" --image screen.png --window region-bottom --dry-run
	$(VENV)/bin/nlp2imgl apply "naciśnij ctrl+enter" --image screen.png --window region-bottom --dry-run
