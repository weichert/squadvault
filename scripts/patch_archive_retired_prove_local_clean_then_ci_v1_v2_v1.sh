#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: archive retired prove_local_clean_then_ci v1/v2 under scripts/_retired (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_archive_retired_prove_local_clean_then_ci_v1_v2_v1.py

"$python" scripts/_patch_archive_retired_prove_local_clean_then_ci_v1_v2_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_archive_retired_prove_local_clean_then_ci_v1_v2_v1.sh

echo "OK"
