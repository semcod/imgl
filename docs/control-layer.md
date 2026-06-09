# Warstwa kontroli `*2imgl`

Zgodnie z [CONTROL_LAYER_PROMPT.template.md](https://github.com/oqlos/doql/blob/main/packages/CONTROL_LAYER_PROMPT.template.md).

## Porty

| Usługa | Port | Użycie |
|--------|------|--------|
| `imgl serve` | 8008 | Web UI — podgląd, miniaturki, agent |
| `rest2imgl serve` | 8219 | REST API — DSL i NL (8218 = rest2coru w Koru) |
| `rest2vql` | 8216 | Capture vql (repo oqlos/vql) |

## Instalacja

```bash
pip install -e ".[web,llm,capture]"
pip install -e packages/dsl2imgl packages/nlp2imgl packages/uri2imgl packages/rest2imgl packages/cli2imgl
```

## Uruchomienie usług

```bash
# Web UI (przeglądarka)
imgl serve --port 8008 --image screen.png --llm --window region-bottom

# REST control API
rest2imgl serve --port 8219

# REPL
cli2imgl

# MCP (Cursor / inne klienty)
mcp2imgl serve
```

Pełny pipeline capture → VQL: [vql-export.md](vql-export.md).

## Faza 4 — Schema + Protobuf + EventStore

`dsl2imgl` utrzymuje trzy reprezentacje komendy:

| Reprezentacja | Lokalizacja |
|---------------|-------------|
| Tekst DSL | `grammar.py`, CLI, URI |
| JSON Schema | `src/dsl2imgl/schema/commands/*.schema.json` |
| Protobuf | `proto/dsl2imgl/v1/command.proto`, `result.proto` |

```bash
# regeneracja *_pb2.py
cd packages/dsl2imgl && bash scripts/generate-proto.sh

# EventStore (commands only, po sukcesie)
.imgl/events/dsl.events.pb
```

REST/MCP akceptują: `text/plain`, `application/json`, `application/x-protobuf`.

## Verby DSL

| Verb | Typ | Opis |
|------|-----|------|
| `HEALTH` | query | Status |
| `CAPTURE` | command | Zrzut ekranu (+ opcjonalnie `--analyze` w CLI) |
| `ANALYZE` | query | OCR + layout + VQL + provenance |
| `ACTIONS` | query | Lista akcji z katalogu |
| `RESOLVE` | query | NL → URI → payload (bez kliku) |
| `CLICK` / `EXECUTE` | command | Klik lub NL z wykonaniem |
| `TYPE` | command | Wpisz tekst w pole |
| `KEY` | command | Skrót klawiszowy (Enter, ctrl+Return) |

## Przykłady DSL

```bash
dsl2imgl exec 'HEALTH'
dsl2imgl exec 'CAPTURE INTERACTIVE'
dsl2imgl exec 'CAPTURE OUT screen.png ANALYZE LANG eng+pol'
dsl2imgl exec 'ACTIONS screen.png WINDOW region-bottom LLM'
dsl2imgl exec 'TYPE "opisz projekt" IN "Chat input" IMAGE screen.png WINDOW region-bottom EXECUTE 1'
dsl2imgl exec 'KEY ctrl+Return EXECUTE 1'
```

## curl (REST)

```bash
curl -s http://127.0.0.1:8219/health
curl -s -X POST http://127.0.0.1:8219/v1/dsl -d 'HEALTH'
curl -s -X POST http://127.0.0.1:8219/v1/nl \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"wpisz test w Chat input","image":"screen.png","window":"region-bottom","execute":true}'
```
