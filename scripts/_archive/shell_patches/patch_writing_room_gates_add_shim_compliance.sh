#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_writing_room_gates_add_shim_compliance.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_writing_room_gates_add_shim_compliance.py"

echo "==> bash syntax check"
bash -n "scripts/patch_writing_room_gates_add_shim_compliance.sh"

echo "OK"
