#!/usr/bin/env bash
# Delegate to vql repo demo (img2nl → VQL fingerprint flow).
set -euo pipefail
VQL_ROOT="${VQL_ROOT:-$HOME/github/oqlos/vql}"
SCRIPT="$VQL_ROOT/examples/img2nl-vql-flow.sh"
if [[ ! -f "$SCRIPT" ]]; then
  echo "Brak $SCRIPT — sklonuj vql: git clone .../oqlos/vql $VQL_ROOT" >&2
  exit 1
fi
exec bash "$SCRIPT" "$@"
