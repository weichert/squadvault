#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: retire local clean-then-ci helpers v1/v2 (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_retire_prove_local_clean_then_ci_v1_v2_v1.py

./scripts/py scripts/_patch_retire_prove_local_clean_then_ci_v1_v2_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_retire_prove_local_clean_then_ci_v1_v2_v1.sh

echo "OK"
