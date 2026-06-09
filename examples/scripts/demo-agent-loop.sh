#!/usr/bin/env bash
# Demo: pętla agenta — capture → analyze → dry-run akcji
# Użycie: examples/scripts/demo-agent-loop.sh
# Wymaga: działający capture (vdisplay mirror lub portal na Wayland)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

OUT="${TMPDIR:-/tmp}/imgl-agent-$(date +%s).png"
WINDOW="${WINDOW:-region-top}"

echo "=== imgl agent loop (dry-run) ==="
echo "Capture + analyze → $OUT"
echo

if ! imgl capture -o "$OUT" --verify --analyze 2>/dev/null; then
  echo "Capture nieudany — używam screen.png z repo"
  OUT="screen.png"
  if [[ ! -f "$OUT" ]]; then
    echo "Brak screen.png — uruchom: make capture-analyze" >&2
    exit 1
  fi
fi

imgl diagnose "$OUT" | head -5
echo

if [[ -f "${OUT%.png}.capture.json" ]]; then
  echo "Provenance: ${OUT%.png}.capture.json"
  head -c 200 "${OUT%.png}.capture.json" 2>/dev/null || true
  echo
  echo
fi

echo "Okna:"
imgl windows "$OUT" 2>&1 | head -20
echo

echo "Dry-run akcji (bez --execute):"
printf 'kliknij Projects\nquit\n' | imgl interact "$OUT" --llm --window "$WINDOW" 2>&1 | tail -25

echo
echo "Pełna pętla z wykonaniem:"
echo "  imgl capture -o step1.png --verify --analyze"
echo "  imgl interact step1.png --llm --window $WINDOW --execute"
echo "  imgl capture -o step2.png --verify --analyze"
echo "  ..."
