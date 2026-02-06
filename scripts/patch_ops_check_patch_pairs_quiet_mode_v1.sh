#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops check_patch_pairs quiet/verbose toggle (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_ops_check_patch_pairs_quiet_mode_v1.py

echo "==> bash syntax check"
bash -n scripts/check_patch_pairs_v1.sh
bash -n scripts/patch_ops_check_patch_pairs_quiet_mode_v1.sh

echo "==> smoke: default (quiet)"
bash scripts/check_patch_pairs_v1.sh | head -n 40

echo "==> smoke: verbose"
SV_PATCH_PAIR_VERBOSE=1 bash scripts/check_patch_pairs_v1.sh | head -n 60

echo "OK"
