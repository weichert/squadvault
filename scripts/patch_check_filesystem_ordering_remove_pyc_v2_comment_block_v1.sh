#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove redundant v2 pyc/__pycache__ SV_PATCH comment block (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_check_filesystem_ordering_remove_pyc_v2_comment_block_v1.py

"$python" scripts/_patch_check_filesystem_ordering_remove_pyc_v2_comment_block_v1.py

echo "==> bash syntax check"
bash -n scripts/check_filesystem_ordering_determinism.sh
bash -n scripts/patch_check_filesystem_ordering_remove_pyc_v2_comment_block_v1.sh

echo "OK"
