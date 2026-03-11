#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix repo-wide wrapper pat quoting (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_fix_repo_wide_wrapper_pat_quote_v1.py

echo "==> bash -n"
bash -n scripts/patch_remove_pythonpath_src_python_literals_repo_wide_v1.sh

echo "==> shim compliance"
bash scripts/check_shims_compliance.sh

echo "OK"
