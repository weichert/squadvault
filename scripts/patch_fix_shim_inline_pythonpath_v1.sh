#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix shim violations (remove inline PYTHONPATH=src + python) (v1) ==="

python="${PYTHON:-python}"
"$python" scripts/_patch_fix_shim_inline_pythonpath_v1.py

echo "==> shim compliance"
bash scripts/check_shims_compliance.sh

echo "==> bash -n"
bash -n scripts/*.sh

echo "OK"
