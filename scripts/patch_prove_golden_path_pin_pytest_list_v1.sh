#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_golden_path pin pytest list (v1) ==="
python="${PYTHON:-python}"
$python scripts/_patch_prove_golden_path_pin_pytest_list_v1.py
echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh
echo "OK"
