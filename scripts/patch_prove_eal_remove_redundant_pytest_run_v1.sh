#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_eal remove redundant pytest run (v1) ==="
python="${PYTHON:-python}"
$python scripts/_patch_prove_eal_remove_redundant_pytest_run_v1.py
echo "==> bash syntax check"
bash -n scripts/prove_eal_calibration_type_a_v1.sh
echo "OK"
