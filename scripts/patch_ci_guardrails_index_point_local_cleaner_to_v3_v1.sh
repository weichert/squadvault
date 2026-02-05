#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI Guardrails Index point local cleaner to v3 (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py

"$python" scripts/_patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.sh

echo "OK"
