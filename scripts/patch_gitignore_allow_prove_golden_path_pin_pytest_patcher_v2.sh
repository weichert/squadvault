#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore allowlist Golden Path pytest pin patcher (v2) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_gitignore_allow_prove_golden_path_pin_pytest_patcher_v2.py

echo "==> verify allowlist present"
grep -n '^\!scripts/_patch_prove_golden_path_pin_pytest_list_v2\.py$' .gitignore >/dev/null
echo "OK"
