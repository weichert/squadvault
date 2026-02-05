#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_golden_path NAC preflight normalization v3 (non-mutating) ==="

python="${PYTHON:-python}"
$python scripts/_patch_prove_golden_path_nac_preflight_normalization_v3.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "OK"
