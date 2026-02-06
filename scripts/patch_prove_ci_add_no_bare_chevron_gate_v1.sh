#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci add no-bare-chevron gate (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_prove_ci_add_no_bare_chevron_gate_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_add_no_bare_chevron_gate_v1.sh

echo "OK"
