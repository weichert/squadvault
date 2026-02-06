#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

echo "==> Gate: no bare '==>' marker lines in scripts/*.sh (v1)"

hits=0

# Scan tracked scripts only (CI-safe).
files="$(git ls-files 'scripts/*.sh' || true)"
if [ -n "$files" ]; then
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if grep -nE '^[[:space:]]*==>' "$f" >/dev/null; then
      echo "ERROR: bare marker(s) found in $f"
      grep -nE '^[[:space:]]*==>' "$f"
      hits=1
    fi
  done <<< "$files"
fi

if [ "$hits" -ne 0 ]; then
  echo "FAIL: replace bare '==>' lines with: echo \"==> ...\""
  exit 1
fi

echo "OK: no bare '==>' markers found."
