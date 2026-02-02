#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci add CWD-independence gate (v2) ==="
python="${PYTHON:-python}"
$python scripts/_patch_prove_ci_add_cwd_independence_gate_v2.py
echo "==> bash -n"
bash -n scripts/prove_ci.sh
echo "OK"
