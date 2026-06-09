# Architektura — kto za co odpowiada

## Projekty

| Projekt | Rola | NL → klik na zrzucie? |
|---------|------|------------------------|
| **imgl** | Zrzut → Scene → katalog → współrzędne → execute | **TAK (rdzeń)** |
| **vql** | Capture portal, `VQLProgram`, bus `vql://window/*` | NIE (infrastruktura) |
| **nlp2uri** (semcod) | NL → `app://`, `file://`, `desktop-*://` | Częściowo (delegacja do imgl) |
| **img2nl** | Opis sceny, blank check | NIE |

## Warstwa kontroli imgl (`packages/`)

Wszystkie adaptery delegują do **`dsl2imgl.dispatch()`** — jeden bus, wiele wejść:

```
nlp2imgl / uri2imgl / cli2imgl / mcp2imgl / rest2imgl
                    ↓
               dsl2imgl.dispatch()
                    ↓
         imgl/capture, pipeline, nlp2uri, execute
```

**Web UI** (`imgl serve :8008`) omija DSL — bezpośrednio używa `imgl/web/session.py`.

## Przepływ `kliknij Projects`

1. `vql` lub `imgl capture` → `screen.png`
2. `imgl analyze` → `Scene`, `layout.vql.json`
3. `imgl/nlp2uri.py` → `vql://window/imgl?action=click&text=Projects`
4. `imgl/interact.resolve_imgl_uri` → `{x, y}`
5. `imgl/execute.py` → xdotool

## Zasada

- **Kontekst zrzutu** (co kliknąć) → zawsze **imgl**
- **Capture / protokół** → **vql**
- **NL ogólny desktop** (otwórz app, plik) → **nlp2uri**
- **Opis obrazu** → **img2nl**

## Integracja z Koru

Koru (`semcod/koru`) używa imgl jako transport wizyjny:

- `koru/integrations/imgl_client.py` — adapter do `nlp2imgl` / `rest2imgl`
- Fallback w `koru auto` gdy plugin koruide padnie (`KORU_IMGL_FALLBACK=1`)
- MCP `koru_desktop_uri_handle` z `transport=imgl`
- Verby `UI_*` w `dsl2coru`

Szczegóły: [koru/docs/imgl-integration.md](https://github.com/semcod/koru/blob/main/docs/imgl-integration.md)
