#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_patch_writing_room_wrapper_set_pythonpath.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_patch_writing_room_wrapper_set_pythonpath.py"

echo "==> bash syntax check"
bash -n "scripts/patch_patch_writing_room_wrapper_set_pythonpath.sh"

echo "OK"
