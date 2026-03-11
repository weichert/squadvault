#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix safe_grep invocations (drop leading -I) (v2) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_fix_safe_grep_invocations_drop_leading_I_v2.py

./scripts/py scripts/_patch_fix_safe_grep_invocations_drop_leading_I_v2.py

echo "==> bash syntax check"
bash -n scripts/check_filesystem_ordering_determinism.sh
bash -n scripts/patch_fix_safe_grep_invocations_drop_leading_I_v2.sh

echo "OK"
