# Skrypty demo

Gotowe skrypty do szybkiego sprawdzenia pipeline imgl na zrzucie ekranu.

## Wymagania

```bash
make install-dev
# opcjonalnie: make install-vdisplay && make install-vql
```

Zalecany pierwszy krok przed demo (VQL + provenance):

```bash
imgl capture -o screen.png --verify --analyze
# lub: make capture-analyze
```

## Skrypty

| Skrypt | Opis |
|--------|------|
| [demo-agent-loop.sh](demo-agent-loop.sh) | capture → diagnose → windows → interact (dry-run) |
| [demo-windows.sh](demo-windows.sh) | wykrywanie regionów + wycinki PNG |
| [demo-github.sh](demo-github.sh) | katalog LLM na regionie GitHub |
| [demo-nlp2uri.py](demo-nlp2uri.py) | NL → `vql://window/imgl?...` (Python) |

## Uruchomienie

```bash
bash examples/scripts/demo-agent-loop.sh
bash examples/scripts/demo-windows.sh screen.png
bash examples/scripts/demo-github.sh screen.png region-top
python examples/scripts/demo-nlp2uri.py screen.png
```

## Powiązane

- [../README.md](../README.md)
- [../../docs/vql-export.md](../../docs/vql-export.md)
- [../workflows/capture-to-action](../workflows/capture-to-action/README.md)
