#!/usr/bin/env bash
# Demo: wykrywanie okien i wycinki PNG
# Użycie: examples/scripts/demo-windows.sh [screen.png]
set -euo pipefail

IMAGE="${1:-screen.png}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "=== imgl windows demo ==="
echo "Obraz: $IMAGE"
echo

imgl windows "$IMAGE" --export-crops --annotate

echo
echo "Wygenerowane pliki:"
ls -1 "${IMAGE%.png}".region-*.png 2>/dev/null || ls -1 screen.region-*.png 2>/dev/null || true

echo
echo "Następny krok:"
echo "  imgl interact $IMAGE --llm --window region-top"
