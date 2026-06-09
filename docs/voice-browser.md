# Głos + przeglądarka

Dwa tryby sterowania przez UI w przeglądarce (`imgl serve :8008`).

## Tryb 1: Web UI + mikrofon przeglądarki

1. Przygotuj zrzut (zalecane):
   ```bash
   make install-dev
   imgl capture -o screen.png --verify --analyze
   ```
2. Uruchom serwer:
   ```bash
   imgl serve --port 8008 --image screen.png --llm --window region-bottom --execute
   ```
3. Otwórz http://127.0.0.1:8008
4. Włącz **Wykonuj na pulpicie**
5. Użyj dyktowania systemowego (GNOME: Super+H) lub rozszerzenia do pola **NL** w UI
6. Wpisz / dyktuj: `wpisz moje pytanie w Chat input` → Enter w UI
7. Dyktuj: `ctrl+enter` lub kliknij akcję **KEY** w przyszłej wersji UI

### Integracja Web Speech API (opcjonalna)

W `imgl/web/static/index.html` można dodać przycisk 🎤:

```javascript
const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
rec.lang = 'pl-PL';
rec.onresult = (e) => {
  const text = e.results[0][0].transcript;
  document.getElementById('nlPrompt').value = text;
};
rec.start();
```

## Tryb 2: Głos → REST → desktop

Asystent głosowy (np. skrypt lokalny) → HTTP → `rest2imgl`:

```bash
rest2imgl serve --port 8219
```

```bash
# Po rozpoznaniu mowy na tekst VOICE_TEXT:
curl -s -X POST http://127.0.0.1:8219/v1/nl \
  -H 'Content-Type: application/json' \
  -d "{\"prompt\":\"$VOICE_TEXT\",\"image\":\"screen.png\",\"window\":\"region-bottom\",\"execute\":true}"
```

Przykład z `whisper` + `curl`:

```bash
VOICE_TEXT=$(whisper audio.wav --language pl --output_format txt -o /tmp | tail -1)
curl -s -X POST http://127.0.0.1:8219/v1/nl \
  -H 'Content-Type: application/json' \
  -d "$(jq -n --arg p "$VOICE_TEXT" '{prompt:$p,image:"screen.png",window:"region-bottom",execute:true}')"
```

## Tryb 3: Agent autonomiczny w przeglądarce

1. http://127.0.0.1:8008
2. Cel: `Otwórz terminal i wpisz pytest`
3. **Pętla** — agent sam: capture → LLM wybiera akcję → execute → capture

Wymaga `OPENROUTER_API_KEY` i zaznaczonego **Zrzut po akcji**.

## Mapowanie komend głosowych → NL

| Mówisz | NL / DSL |
|--------|----------|
| „kliknij Projects” | `kliknij Projects` |
| „wpisz test w chat” | `wpisz test w Chat input` |
| „wyślij” / „enter” | `KEY Return` |
| „ctrl enter” / „wyślij wiadomość” | `KEY ctrl+Return` |
| „nowy zrzut” | `CAPTURE INTERACTIVE` |

## Bezpieczeństwo

Domyślnie **dry-run**. Głos + `--execute` wykonuje prawdziwe kliknięcia — używaj tylko na zaufanym stanowisku.

Zobacz też: [web-ui.md](web-ui.md), [vql-export.md](vql-export.md), [examples/workflows/web-ui](../examples/workflows/web-ui/README.md).
