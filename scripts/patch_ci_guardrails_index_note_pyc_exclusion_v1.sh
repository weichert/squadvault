#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI Guardrails Index — note pyc/__pycache__ exclusion (v1) ==="

python="${PYTHON:-python}"

echo "==> py_compile patcher"
"$python" -m py_compile scripts/_patch_ci_guardrails_index_note_pyc_exclusion_v1.py

./scripts/py scripts/_patch_ci_guardrails_index_note_pyc_exclusion_v1.py

echo "==> bash syntax check"
bash -n scripts/patch_ci_guardrails_index_note_pyc_exclusion_v1.sh

echo "OK"
