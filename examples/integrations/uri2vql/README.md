# Integracja: uri2vql

`uri2vql` rozpoznaje URI `vql://window/imgl?...` i deleguje do imgl.

## Instalacja

```bash
pip install -e ~/github/semcod/imgl
pip install -e ~/github/oqlos/vql/packages/uri2vql
# lub: pip install -e ~/github/oqlos/vql/packages/uri2vql[imgl]
pip install -e ~/github/wronai/vdisplay[pillow]   # opcjonalnie: provenance capture + window_os
```

## Akcje URI

| action | Parametry | Wynik |
|--------|-----------|-------|
| `analyze` | `image`, `file`, `lang` | VQL program + metadata |
| `list` | jw. | katalog elementów JSON |
| `click` | `text`, `element_id`, `window` | `{action, x, y, image_path, ...}` |
| `type` | `value`, `label`, `element_id` | `{action, x, y, text, image_path}` |
| `annotate` | `output` | ścieżka PNG z numerami |

## Przykłady

```bash
# Capture + VQL (imgl)
imgl capture -o screen.png --verify --analyze

# Analiza przez uri2vql
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&lang=eng%2Bpol&action=analyze'

# Lista elementów
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&action=list&lang=eng%2Bpol'

# Klik
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&action=click&text=Save&lang=eng%2Bpol'

# Mapa numerów
uri2vql query 'vql://window/imgl?image=/tmp/screen.png&file=layout.vql.json&action=annotate&lang=eng%2Bpol'
```

## adopt-imgl (jednorazowy eksport VQL)

```bash
uri2vql adopt-imgl --image screen.png --out layout.vql.json --lang eng+pol
```

Eksport imgl zawiera (od wersji z `capture_provenance`):

- `metadata.capture` — provenance z `screen.capture.json` (method, display, monitor)
- `metadata.window_os` — korelacja okien vdisplay ↔ vision (gdy vdisplay zainstalowany)
- `scene.relations` — `contains` (okno → element UI)

## Cache sceny

Przy `action=list|click|type` uri2vql używa `load_or_analyze` + cache `*.vql.imgl.json` — ponowne zapytania bez pełnego OCR.

Przy nowym PNG cache VQL i `.capture.json` są invalidowane.

## Ograniczenie

Handler uri2vql buduje katalog na **całym** zrzucie (bez `window_scope` picker). Do pracy per-region użyj CLI:

```bash
imgl interact screen.png --llm --window region-top
```

lub Python API z `window_id=`.

## Powiązane

- [docs/vql-export.md](../../../docs/vql-export.md)
- [integrations/nlp2uri](../nlp2uri/README.md)
- [integrations/python-api](../python-api/README.md)
