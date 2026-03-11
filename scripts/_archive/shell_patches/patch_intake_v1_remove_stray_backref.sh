#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_intake_v1_remove_stray_backref.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_intake_v1_remove_stray_backref.py"

echo "==> bash syntax check"
bash -n "scripts/patch_intake_v1_remove_stray_backref.sh"

echo "OK"
