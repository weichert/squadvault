#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_selection_set_schema_add_deterministic_helpers.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_selection_set_schema_add_deterministic_helpers.py"

echo "==> bash syntax check"
bash -n "scripts/patch_selection_set_schema_add_deterministic_helpers.sh"

echo "OK"
