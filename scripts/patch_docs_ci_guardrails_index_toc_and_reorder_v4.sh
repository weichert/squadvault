#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: CI Guardrails Index reorder HowTo/OperatorSafety/Contents (v4) ==="

./scripts/py -m py_compile scripts/_patch_docs_ci_guardrails_index_toc_and_reorder_v4.py
./scripts/py scripts/_patch_docs_ci_guardrails_index_toc_and_reorder_v4.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_ci_guardrails_index_toc_and_reorder_v4.sh

echo "==> verify single headings"
n_contents=$(grep -c "^## Contents$" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true)
n_how=$(grep -c "^## How to Read This Index$" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true)
n_ops=$(grep -c "^## Operator Safety Note (Build Mode)$" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true)
echo "Contents count: $n_contents"
echo "How-to-read count: $n_how"
echo "Operator Safety count: $n_ops"
test "$n_contents" -eq 1
test "$n_how" -eq 1
test "$n_ops" -eq 1

echo "==> preview top"
sed -n '1,140p' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
