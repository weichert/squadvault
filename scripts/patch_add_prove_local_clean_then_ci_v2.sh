#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add prove_local_clean_then_ci_v2 helper (v2) ==="

python="${PYTHON:-python}"
"$python" scripts/_patch_add_prove_local_clean_then_ci_v2.py

chmod +x scripts/prove_local_clean_then_ci_v2.sh

echo "==> bash syntax check"
bash -n scripts/prove_local_clean_then_ci_v2.sh
bash -n scripts/patch_add_prove_local_clean_then_ci_v2.sh

echo "OK"
