#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add prove_local_clean_then_ci_v1 helper (v1) ==="

python="${PYTHON:-python}"
"$python" scripts/_patch_add_prove_local_clean_then_ci_v1.py

chmod +x scripts/prove_local_clean_then_ci_v1.sh

echo "==> bash syntax check"
bash -n scripts/prove_local_clean_then_ci_v1.sh
bash -n scripts/patch_add_prove_local_clean_then_ci_v1.sh

echo "OK"
