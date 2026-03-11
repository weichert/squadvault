#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: tidy CI Guardrails Index spacing (v1) ==="

./scripts/py scripts/_patch_docs_tidy_ci_guardrails_index_spacing_v1.py

echo "==> bash -n wrapper"
bash -n scripts/patch_docs_tidy_ci_guardrails_index_spacing_v1.sh

echo "==> preview relevant section"
sed -n '70,140p' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
