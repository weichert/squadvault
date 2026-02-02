#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove prove_ci step from add-pytest wrapper (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_remove_prove_ci_step_from_patch_add_pytest_wrapper_v1.py

echo "==> bash -n"
bash -n scripts/patch_add_pytest_to_requirements_v1.sh

echo "OK"
