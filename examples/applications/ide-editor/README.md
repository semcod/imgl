# Zastosowanie: IDE (Windsurf / VS Code / Cursor)

Sterowanie edytorem kodu na dolnej części zrzutu — **`region-bottom`**.

## Kontekst

IDE zajmuje dolną połowę pionowego zrzutu:

```bash
imgl windows screen.png --export-crops
# → screen.region-bottom.png
```

Widać: eksplorator plików, edytor, terminal, panel AI (Cascade).

## Analiza regionu IDE

```bash
imgl capture -o screen.png --verify --analyze   # gdy potrzebny świeży zrzut
imgl interact screen.png --llm --window region-bottom
```

Typowe elementy w katalogu:

| Typ | Przykłady |
|-----|-----------|
| button | Terminal, Local (2), nazwy plików w explorerze |
| input | pasek wyszukiwania, pole w terminalu |
| toolbar | ikony paska bocznego |

## Przykłady akcji

```
kliknij Terminal          # fokus na terminal
23                        # numer z katalogu (zmienia się między runami!)
mapa
```

W terminalu (po `--execute` + fokus):

```
# UWAGA: imgl nie wysyła Enter/skrótów — tylko click i type
# Wpisz komendę przez type:
wpisz pytest w pole terminalu
```

## Ograniczenia IDE

| Co działa | Co nie |
|-----------|--------|
| Klik w widoczny tekst/przycisk | Skróty Ctrl+Shift+P |
| Wpisanie tekstu w fokusowany input | Tab między panelami |
| Numer z katalogu | Przeciąganie, scroll |

## Lepsza strategia dla IDE

1. **Klik** w plik w explorerze (np. `layout.py`)
2. **Capture** po otwarciu pliku
3. **Klik** w edytorze / użyj API edytora zamiast pikseli

Dla automatyzacji IDE rozważ MCP/Extension zamiast samego imgl.

## find bez LLM

```bash
imgl find screen.png --window region-bottom --text Terminal --click
imgl find screen.png --window region-bottom --list
```

## Powiązane

- [docs/capture.md](../../../docs/capture.md)
- [workflows/multi-step-agent](../../workflows/multi-step-agent/README.md)
- [platforms/gnome-wayland](../../platforms/gnome-wayland/README.md)
