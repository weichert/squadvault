#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_deprecate_week6_shim_patcher.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_deprecate_week6_shim_patcher.py"

echo "==> bash syntax check"
bash -n "scripts/patch_deprecate_week6_shim_patcher.sh"

echo "OK"
