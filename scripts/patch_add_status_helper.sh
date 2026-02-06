#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_add_status_helper.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_add_status_helper.py"

echo "==> bash syntax check"
bash -n "scripts/patch_add_status_helper.sh"

echo "OK"
