#!/usr/bin/env bash
# Demo: katalog LLM dla regionu GitHub (region-top)
# Użycie: examples/scripts/demo-github.sh [screen.png]
set -euo pipefail

IMAGE="${1:-screen.png}"
WINDOW="${2:-region-top}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== imgl GitHub demo (window=$WINDOW) ==="

if [[ -z "${OPENROUTER_API_KEY:-}" ]] && [[ ! -f .env ]]; then
  echo "UWAGA: brak OPENROUTER_API_KEY — użyje fallback OCR"
fi

printf 'lista\nquit\n' | imgl interact "$IMAGE" --llm --window "$WINDOW" 2>&1 | head -60

echo
echo "Interaktywnie:"
echo "  imgl interact $IMAGE --llm --window $WINDOW --annotate --open"
