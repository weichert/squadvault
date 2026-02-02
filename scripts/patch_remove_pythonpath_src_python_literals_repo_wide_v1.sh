#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove literal PYTHONPATH=src + python substrings repo-wide (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_remove_pythonpath_src_python_literals_repo_wide_v1.py

echo "==> sanity: grep should find none (repo-wide; excluding shim checker)"
git ls-files | grep -v "^scripts/check_shims_compliance\.sh$" | \
  pat="PYTHONPATH=src ""python""; \
  xargs grep -n "$pat" \
  && { echo "ERROR: still found literal substring"; exit 2; } \
  || echo "OK: substring not present anywhere except shim checker"

echo "==> shim compliance"
bash scripts/check_shims_compliance.sh

echo "==> bash -n"
bash -n scripts/*.sh

echo "OK"
