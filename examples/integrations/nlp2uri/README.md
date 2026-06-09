# Integracja: nlp2uri (NL → URI)

Warstwa tłumacząca język naturalny i numery na `vql://window/imgl?...`.

## W shellu imgl interact

```bash
imgl interact screen.png --llm --window region-top
```

| Wejście | match_reason | URI action |
|---------|--------------|------------|
| `3` | `catalog:index` | click z katalogu |
| `kliknij Save` | `catalog:text` | click po etykiecie |
| `wpisz hello w Username` | `type` | type + value |
| `lista` | `list` | odśwież katalog |
| `mapa` | `annotate` | PNG z numerami |
| `quit` | `quit` | wyjście |

## Python API

```python
from imgl.catalog import build_interactive_catalog
from imgl.nlp2uri import prompt_to_imgl_uri
from imgl import analyze

scene = analyze("screen.png", lang="eng+pol")
catalog = build_interactive_catalog(scene, image_path="screen.png")

resolved = prompt_to_imgl_uri(
    "kliknij Projects",
    image="screen.png",
    file="layout.vql.json",
    lang="eng+pol",
    catalog=catalog,
)
print(resolved.uri)
print(resolved.confidence, resolved.match_reason)
```

## Skrypt demo

```bash
python examples/scripts/demo-nlp2uri.py screen.png
```

## Reguły dopasowania (kolejność)

1. Numer (`3`, `nr 5`)
2. `quit`, `mapa`, `lista`, `analizuj`
3. **`kliknij X`** — przed type (fix: „Type to search” nie myli się z `type`)
4. **`wpisz X w pole Y`** / `type X in field Y`
5. Fuzzy dopasowanie do katalogu
6. Fallback → `uri2vql.nlp2uri` (jeśli zainstalowany)

## Najlepsze praktyki

```bash
# DOBRZE — unikalna etykieta
kliknij Follow
kliknij Projects

# DOBRZE — numer
9

# DOBRZE — type z etykietą z katalogu
wpisz semcod w Type to search

# SŁABO — ogólne słowo
kliknij button
wpisz test w search
```

## Powiązane

- [docs/vql-export.md](../../../docs/vql-export.md)
- [workflows/multi-step-agent](../../workflows/multi-step-agent/README.md)
- [integrations/uri2vql](../uri2vql/README.md)
