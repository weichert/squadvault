#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_ops_shims_cwd_polish_oneshot_v1.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_ops_shims_cwd_polish_oneshot_v1.py"

echo "==> bash syntax check"
bash -n "scripts/patch_ops_shims_cwd_polish_oneshot_v1.sh"

echo "OK"
