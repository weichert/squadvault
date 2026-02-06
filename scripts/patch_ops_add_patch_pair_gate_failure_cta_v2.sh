#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add pairing gate failure CTA (v2) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ops_add_patch_pair_gate_failure_cta_v2.py

echo "==> bash syntax check (spot)"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/patch_ops_add_patch_pair_gate_failure_cta_v2.sh

echo "==> smoke: pairing gate (verbose)"
SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh | tail -n 60

echo "OK"
