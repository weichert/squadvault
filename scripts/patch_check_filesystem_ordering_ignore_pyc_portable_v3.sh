#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: filesystem ordering gate ignore __pycache__/ + *.pyc (portable v3) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_check_filesystem_ordering_ignore_pyc_portable_v3.py

"$python" scripts/_patch_check_filesystem_ordering_ignore_pyc_portable_v3.py

echo "==> bash syntax check"
bash -n scripts/check_filesystem_ordering_determinism.sh
bash -n scripts/patch_check_filesystem_ordering_ignore_pyc_portable_v3.sh

echo "OK"
