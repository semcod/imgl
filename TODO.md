# TODO — imgl

## Zrobione (0.7.x)

- [x] `window_scope` — region-top / region-bottom
- [x] `imgl serve` web UI :8008
- [x] LLM catalog + merge pól input z OCR
- [x] `execute` KEY (Enter, ctrl+Return)
- [x] `packages/*2imgl` — dsl, uri, nlp, cli, mcp, rest (8219)
- [x] `dsl2imgl` Faza 4 — JSON Schema + Protobuf + EventStore
- [x] `docs/*` — architektura, NL shell, głos, control layer

## W toku / następne
- [ ] `uri2vql` handler: `window_scope` w `vql://window/imgl`
- [ ] Web UI: przycisk mikrofonu (Web Speech API)
- [ ] Web UI: akcja KEY w panelu (Enter / Ctrl+Enter)
- [ ] `execute`: Tab, skróty, ydotool key combos (Wayland)
- [ ] `nlp2uri` (semcod): oficjalna delegacja `desktop-window` → `uri2imgl`
- [ ] Testy parity: dsl2imgl = rest2imgl = mcp2imgl

## Znane ograniczenia

- Współrzędne ze statycznego PNG — wymagaj świeżego capture po akcji
- Wayland: xdotool ograniczony; portal tylko do capture
- Placeholder „Add a follow-up” często bez OCR — używaj etykiety **Chat input**
