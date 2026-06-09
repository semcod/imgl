# Web UI — tryb manualny i autonomiczny

Usługa HTTP na porcie **8008** z podglądem zrzutu, listą akcji (miniaturki) i pętlą agenta.

## Instalacja

```bash
cd ~/github/semcod/imgl
source .venv/bin/activate
make install-dev                    # vdisplay + capture
pip install -e ".[web,llm,capture]"
```

## Uruchomienie

```bash
# Najpierw zrzut + VQL (opcjonalnie — serve może capture-on-start)
imgl capture -o screen.png --verify --analyze

imgl serve --port 8008 --image screen.png
# GitHub (górny region) + LLM:
imgl serve --port 8008 --image screen.png --llm --window region-top
# pełny tryb:
imgl serve --port 8008 --image screen.png --execute --llm --window region-top --capture-on-start
```

Otwórz: **http://127.0.0.1:8008**

## Tryb manualny

1. **Zrzut ekranu** — przycisk lub `POST /api/capture` (vdisplay → PNG + analiza → VQL)
2. Wybierz **region okna** (dropdown)
3. Lista **akcji z miniaturkami** — kliknij numer lub kartę
4. Pole **NL** — np. `kliknij Projects`, `wpisz hello w Type to search`
5. Po każdej akcji (gdy włączone *Zrzut po akcji*) — nowy capture + analiza + odświeżenie katalogu

Sesja web zapisuje `layout.vql.json` i cache Scene obok obrazu (jak CLI `interact`).

## Tryb autonomiczny

1. Wpisz **cel** (np. „Otwórz zakładkę Projects”)
2. **Start** — przygotowanie agenta
3. **1 krok** — LLM wybiera akcję z katalogu, wykonuje, odświeża zrzut
4. **Pętla** — do `max_steps` kroków

Wymaga `OPENROUTER_API_KEY` w `.env` lub środowisku.

## API (skrót)

| Endpoint | Opis |
|----------|------|
| `GET /api/state` | Stan: akcje, okna, historia, `vql_file` |
| `GET /api/screenshot` | Aktualny PNG |
| `GET /api/annotated` | Mapa z numerami |
| `GET /api/actions/{n}/thumb` | Miniatura elementu |
| `POST /api/capture` | Nowy zrzut + analiza + VQL |
| `POST /api/act` | `{index}` lub `{prompt}` |
| `POST /api/agent/start` | `{goal, max_steps}` |
| `POST /api/agent/step` | Jeden krok agenta |
| `POST /api/agent/run` | Pełna pętla w jednym żądaniu |

## Uwagi

- **Wayland**: capture próbuje vdisplay mirror; przy `--capture-on-start` może pojawić się portal GNOME (fallback)
- Współrzędne są ze **świeżego** zrzutu — włącz „Zrzut po akcji”
- Domyślnie **dry-run** — zaznacz „Wykonuj na pulpicie” dla xdotool/ydotool
- Przy execute obowiązuje guard DISPLAY (jak CLI) — patrz [vql-export.md](vql-export.md)

## Powiązane

- [docs/web-ui.md](../../docs/web-ui.md)
- [docs/vql-export.md](../../docs/vql-export.md)
- [workflows/multi-step-agent](../multi-step-agent/README.md)
