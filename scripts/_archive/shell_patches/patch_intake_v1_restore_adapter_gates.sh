#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: scripts/patch_intake_v1_restore_adapter_gates.sh ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" "scripts/_patch_intake_v1_restore_adapter_gates.py"

echo "==> bash syntax check"
bash -n "scripts/patch_intake_v1_restore_adapter_gates.sh"

echo "OK"
