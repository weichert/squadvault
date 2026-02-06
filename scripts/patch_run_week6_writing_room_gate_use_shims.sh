#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_run_week6_writing_room_gate_use_shims.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_run_week6_writing_room_gate_use_shims.py"

echo "==> bash syntax check"
bash -n "scripts/patch_run_week6_writing_room_gate_use_shims.sh"

echo "OK"
