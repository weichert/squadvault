#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: .gitignore allowlist prove_eal redundant pytest patcher (v1) ==="
python="${PYTHON:-python}"
$python scripts/_patch_gitignore_allow_prove_eal_redundant_pytest_patcher_v1.py
echo "OK"
