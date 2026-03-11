#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix executable modes under scripts/_retired (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_fix_modes_in_retired_v1.py

./scripts/py scripts/_patch_fix_modes_in_retired_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_fix_modes_in_retired_v1.sh

echo "OK"
