#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: harden fix_modes_in_retired to recurse (rglob) (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_harden_fix_modes_in_retired_rglob_v1.py

"$python" scripts/_patch_harden_fix_modes_in_retired_rglob_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_harden_fix_modes_in_retired_rglob_v1.sh

echo "==> py_compile target (post-patch)"
"$python" -m py_compile scripts/_patch_fix_modes_in_retired_v1.py

echo "OK"
