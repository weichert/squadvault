#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove shim-forbidden literal from sanitize-wrapper grep (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_fix_shim_checker_literal_in_sanitize_wrapper_v1.py

echo "==> bash -n"
bash -n scripts/patch_sanitize_pythonpath_src_python_literals_in_patchers_v1.sh

echo "==> shim compliance"
bash scripts/check_shims_compliance.sh

echo "OK"
