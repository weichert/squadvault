#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix gitignore allowlist wrapper script (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_fix_patch_gitignore_allow_prove_golden_path_wrapper_v1.py

echo "==> shellcheck: bash -n"
bash -n scripts/patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v1.sh
echo "OK"
