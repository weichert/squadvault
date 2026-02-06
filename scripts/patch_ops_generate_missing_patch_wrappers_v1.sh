#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops generate missing patch wrappers (v1) ==="

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [ -x "./scripts/py" ]; then
  PY="./scripts/py"
else
  PY="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ops_generate_missing_patch_wrappers_v1.py

echo "==> bash syntax check (spot)"
bash -n scripts/patch_ops_generate_missing_patch_wrappers_v1.sh

echo "==> smoke: pairing gate (quiet)"
bash scripts/check_patch_pairs_v1.sh | head -n 40

echo "OK"
