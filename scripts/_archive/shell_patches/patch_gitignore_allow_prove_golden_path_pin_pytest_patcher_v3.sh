#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore allowlist Golden Path pytest pin patcher (v3) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v3.py
grep -n '^\!scripts/_patch_prove_golden_path_pin_pytest_list_v3\.py$' .gitignore >/dev/null
echo "OK"
