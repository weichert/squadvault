#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: sanitize PYTHONPATH=src + python literal in patchers + wrapper text (v1) ==="
python="${PYTHON:-python}"
"$python" scripts/_patch_sanitize_pythonpath_src_python_literals_in_patchers_v1.py

echo "==> sanity: repo-wide grep (excluding shim checker) should now be clean"
git ls-files | grep -v '^scripts/check_shims_compliance\.sh$' | \
  xargs grep -n 'PYTHONPATH=src python' \
  && { echo "ERROR: still found contiguous literal"; exit 2; } \
  || echo "OK: contiguous literal not present outside shim checker"

echo "==> shim compliance"
bash scripts/check_shims_compliance.sh

echo "==> bash -n"
bash -n scripts/*.sh

echo "OK"
