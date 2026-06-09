SHELL := /usr/bin/env bash

PYTHON ?= python3
VENV ?= .venv
PIP := $(VENV)/bin/pip
PY := $(VENV)/bin/python

IMGL_IMAGE ?= screen.png
IMGL_WINDOW ?= region-bottom
REST_PORT ?= 8219
WEB_PORT ?= 8008

.PHONY: help venv install install-dev install-control install-full test test-dsl2imgl \
	capture proto serve-rest serve-web demo-key demo-nl demo-chat

help:
	@echo "imgl — Makefile"
	@echo ""
	@echo "Instalacja:"
	@echo "  make venv              utwórz .venv"
	@echo "  make install           pip install -e ."
	@echo "  make install-dev       + [dev,llm,capture]"
	@echo "  make install-control   + packages/dsl2imgl nlp2imgl rest2imgl"
	@echo "  make install-full      dev + control + [web]"
	@echo ""
	@echo "Testy:"
	@echo "  make test              pytest cały projekt"
	@echo "  make test-dsl2imgl     pytest packages/dsl2imgl"
	@echo ""
	@echo "Usługi:"
	@echo "  make capture           zrzut → $(IMGL_IMAGE)"
	@echo "  make serve-rest        rest2imgl :$(REST_PORT)"
	@echo "  make serve-web         imgl serve :$(WEB_PORT)"
	@echo ""
	@echo "Demo (wymaga zrzutu + xdotool do --execute):"
	@echo "  make demo-key          KEY ctrl+Return (dry-run)"
	@echo "  make demo-nl           nlp2imgl TYPE w Chat input"
	@echo "  make demo-chat         TYPE + KEY (dry-run)"
	@echo ""
	@echo "Protobuf:"
	@echo "  make proto             regenerate dsl2imgl *_pb2.py"

venv:
	@test -x "$(PY)" || $(PYTHON) -m venv "$(VENV)"

install: venv
	$(PIP) install -e .

install-dev: install
	$(PIP) install -e ".[dev,llm,capture]"

install-control: install-dev
	$(PIP) install -e packages/dsl2imgl packages/nlp2imgl packages/rest2imgl packages/cli2imgl

install-full: install-control
	$(PIP) install -e ".[web]"

test:
	$(PY) -m pytest tests packages/dsl2imgl/tests -q

test-dsl2imgl:
	$(PY) -m pytest packages/dsl2imgl/tests -q

capture:
	$(PY) -m imgl.cli capture --interactive -o $(IMGL_IMAGE)

proto:
	bash packages/dsl2imgl/scripts/generate-proto.sh

serve-rest: install-control
	$(VENV)/bin/rest2imgl serve --port $(REST_PORT)

serve-web: install-full
	$(PY) -m imgl.cli serve --port $(WEB_PORT) --image $(IMGL_IMAGE) --llm --window $(IMGL_WINDOW)

demo-key: install-control
	$(VENV)/bin/dsl2imgl exec 'KEY ctrl+Return EXECUTE 0'

demo-nl: install-control
	@test -f "$(IMGL_IMAGE)" || (echo "Brak $(IMGL_IMAGE) — uruchom: make capture" && exit 1)
	$(VENV)/bin/nlp2imgl apply "wpisz test w Chat input" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW)

demo-chat: install-control
	@test -f "$(IMGL_IMAGE)" || (echo "Brak $(IMGL_IMAGE) — uruchom: make capture" && exit 1)
	$(VENV)/bin/nlp2imgl apply "wpisz demo w Chat input" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW)
	$(VENV)/bin/nlp2imgl apply "naciśnij ctrl+enter" --image $(IMGL_IMAGE) --window $(IMGL_WINDOW)
