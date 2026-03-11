#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: harden CI guardrails index wrapper with py_compile (v1) ==="

python="${PYTHON:-python}"
./scripts/py scripts/_patch_harden_patch_ci_guardrails_index_wrapper_pycompile_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_ci_guardrails_index_point_local_cleaner_to_v3_v1.sh
bash -n scripts/patch_harden_patch_ci_guardrails_index_wrapper_pycompile_v1.sh

echo "OK"
