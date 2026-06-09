# Workflow: pętla agenta (multi-step)

Sterowanie UI wymaga **świeżego zrzutu po każdej akcji** — współrzędne z poprzedniego kroku szybko się dezaktualizują.

## Wzorzec

```
┌─────────────┐
│  capture    │
└──────┬──────┘
       ▼
┌─────────────┐
│ windows /   │  opcjonalnie: wybierz region
│ interact    │
└──────┬──────┘
       ▼
┌─────────────┐
│ NL / numer  │  → URI → {action, x, y}
└──────┬──────┘
       ▼
┌─────────────┐
│ execute     │  opcjonalnie: xdotool
└──────┬──────┘
       │
       └──────► capture (ponownie)
```

## Skrypt demonstracyjny

```bash
examples/scripts/demo-agent-loop.sh
```

## Ręczna pętla (3 kroki)

```bash
# Krok A — otwórz zakładkę
imgl capture --interactive -o s1.png
imgl interact s1.png --llm --window region-top --execute <<<'3'   # Projects

# Krok B — poczekaj na UI, nowy zrzut
sleep 1
imgl capture --interactive -o s2.png
imgl interact s2.png --llm --window region-top --execute <<<'kliknij Repositories'

# Krok C — wpisz w search
imgl capture --interactive -o s3.png
imgl interact s3.png --llm --window region-top --execute <<<'wpisz imgl w Type to search'
```

## Python — agent z API

```python
from imgl import analyze, actions
from imgl.catalog import build_interactive_catalog
from imgl.nlp2uri import prompt_to_imgl_uri
from imgl.interact import InteractSession, resolve_imgl_uri
from imgl.execute import execute_action
from imgl.window_scope import apply_discovered_windows

def act_on_screenshot(image: str, prompt: str, *, window_id: str = "region-top", execute: bool = False):
    scene = analyze(image, lang="eng+pol")
    scene = apply_discovered_windows(scene)
    session = InteractSession(
        image_path=image,
        vql_file="layout.vql.json",
        lang="eng+pol",
        scene=scene,
        catalog=[],
        selected_window_id=window_id,
        use_llm=True,
    )
    session.catalog = build_interactive_catalog(
        scene,
        image_path=image,
        vql_file="layout.vql.json",
        lang="eng+pol",
        window_id=window_id,
        use_llm=True,
    )
    resolved = prompt_to_imgl_uri(prompt, image=image, catalog=session.catalog)
    if not resolved:
        raise ValueError(f"Nie rozumiem: {prompt}")
    result = resolve_imgl_uri(resolved.uri, session)
    if not result.get("ok"):
        raise RuntimeError(result.get("error"))
    if execute:
        execute_action({k: v for k, v in result.items() if k not in {"ok", "uri_action"}}, dry_run=False)
    return result

# act_on_screenshot("screen.png", "kliknij Follow", execute=True)
```

## Integracja z uri2vql / agentem zewnętrznym

Agent (Cursor, koru, własny skrypt) może:

1. `uri2vql query 'vql://window/imgl?...&action=list'` — pobierz katalog
2. `nlp2uri` / numer — wybierz akcję
3. `uri2vql query '...&action=click&element_id=...'` — payload
4. Własne wykonanie lub `imgl --execute`

## Najpewniejsze metody wyboru

| Metoda | Niezawodność |
|--------|--------------|
| Numer z katalogu (`3`) | najwyższa |
| `kliknij UnikalnaEtykieta` | wysoka, gdy etykieta unikalna |
| `wpisz X w Pole` | średnia — wymaga dopasowania label |
| Fuzzy NL | zmienna |

## Powiązane

- [integrations/nlp2uri](../../integrations/nlp2uri/README.md)
- [integrations/uri2vql](../../integrations/uri2vql/README.md)
