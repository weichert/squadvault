#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops fix prove_ci suite header dangling quote (v4) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_ops_fix_prove_ci_suite_header_block_v4.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_ops_fix_prove_ci_suite_header_block_v4.sh

echo "OK"
