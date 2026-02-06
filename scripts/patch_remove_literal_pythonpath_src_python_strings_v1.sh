#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove literal 'PYTHONPATH=src + python' substrings from helper scripts (v1) ==="
python="${PYTHON:-python}"
./scripts/py scripts/_patch_remove_literal_pythonpath_src_python_strings_v1.py

echo "==> shim compliance"
bash scripts/check_shims_compliance.sh

echo "==> sanity grep (should NOT hit patch_ci_shim_violations or patch_fix wrapper banners)"
grep -n "PYTHONPATH=src + python" scripts/*.sh || echo "OK: no inline PYTHONPATH=src + python substring in scripts/*.sh (except checker comments may still mention it)"

echo "OK"
