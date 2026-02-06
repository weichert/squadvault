#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: clarify CI Guardrails Index reading + enforcement scope (v1) ==="

./scripts/py -m py_compile scripts/_patch_docs_clarify_ci_guardrails_index_reading_v1.py
./scripts/py scripts/_patch_docs_clarify_ci_guardrails_index_reading_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_clarify_ci_guardrails_index_reading_v1.sh

echo "==> preview top of index"
sed -n '1,90p' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
