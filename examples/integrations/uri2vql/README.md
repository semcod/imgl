# Integracja: uri2vql

`uri2vql` rozpoznaje URI `vql://window/imgl?...` i deleguje do imgl.

## Instalacja

```bash
pip install -e ~/github/semcod/imgl
pip install -e ~/github/oqlos/vql/packages/uri2vql
# lub: pip install -e ~/github/oqlos/vql/packages/uri2vql[imgl]
```

## Akcje URI

| action | Parametry | Wynik |
|--------|-----------|-------|
| `analyze` | `image`, `file`, `lang` | VQL program + metadata |
| `list` | jw. | katalog elementów JSON |
| `click` | `text`, `element_id`, `window` | `{action, x, y, ...}` |
| `type` | `value`, `label`, `element_id` | `{action, x, y, text}` |
| `annotate` | `output` | ścieżka PNG z numerami |

## Przykłady

```bash
# Analiza
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

## Cache sceny

Przy `action=list|click|type` uri2vql używa `load_or_analyze` + cache `layout.imgl.json` — ponowne zapytania bez pełnego OCR.

## Ograniczenie

Handler uri2vql buduje katalog na **całym** zrzucie (bez `window_scope` picker). Do pracy per-region użyj CLI:

```bash
imgl interact screen.png --llm --window region-top
```

lub Python API z `window_id=`.

## Powiązane

- [integrations/nlp2uri](../nlp2uri/README.md)
- [integrations/python-api](../python-api/README.md)
