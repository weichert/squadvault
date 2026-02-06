#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore allowlist Golden Path pytest pin patcher (v1) ==="
python="${PYTHON:-python}"

./scripts/py scripts/_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v1.py

echo "==> verify allowlist present"
grep -n '^\!scripts/_patch_prove_golden_path_pin_pytest_list_v1\.py$' .gitignore >/dev/null
echo "OK"
