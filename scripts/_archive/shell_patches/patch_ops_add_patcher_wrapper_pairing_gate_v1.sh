#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops add patcher/wrapper pairing gate (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ops_add_patcher_wrapper_pairing_gate_v1.py

echo "==> bash syntax check"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/prove_ci.sh
bash -n scripts/patch_ops_add_patcher_wrapper_pairing_gate_v1.sh

echo "OK"
