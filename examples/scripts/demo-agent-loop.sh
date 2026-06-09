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
echo "Capture → $OUT"
echo

if ! imgl capture -o "$OUT" --verify 2>/dev/null; then
  echo "Capture nieudany — używam screen.png z repo"
  OUT="screen.png"
fi

imgl diagnose "$OUT" | head -5
echo

echo "Okna:"
imgl windows "$OUT" 2>&1 | head -20
echo

echo "Dry-run akcji (bez --execute):"
printf 'kliknij Projects\nquit\n' | imgl interact "$OUT" --llm --window "$WINDOW" 2>&1 | tail -25

echo
echo "Pełna pętla z wykonaniem:"
echo "  imgl capture -o step1.png --verify"
echo "  imgl interact step1.png --llm --window $WINDOW --execute"
echo "  imgl capture -o step2.png --verify"
echo "  ..."
