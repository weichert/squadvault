#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore allowlist Golden Path remove-pytest-dir patcher (v2) ==="
python="${PYTHON:-python}"

"$python" scripts/_patch_gitignore_allow_prove_golden_path_remove_pytest_dir_invocation_patcher_v2.py

grep -n '^\!scripts/_patch_prove_golden_path_remove_pytest_dir_invocation_v2\.py$' .gitignore >/dev/null
echo "OK"
