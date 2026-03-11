#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_golden_path ephemeral exports by default (v1) ==="

python="${PYTHON:-python}"
./scripts/py scripts/_patch_prove_golden_path_ephemeral_exports_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "OK"
