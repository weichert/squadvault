#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_golden_path pin pytest list (v2; bash3-safe; no dir fallback) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_prove_golden_path_pin_pytest_list_v2.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh
echo "OK"
