#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs discoverability links for canonical patcher/wrapper pattern (v1) ==="

PY="./scripts/py"
if [[ ! -x "$PY" ]]; then
  PY="${PYTHON:-python}"
fi

"$PY" scripts/_patch_docs_add_patcher_wrapper_links_v1.py

echo "==> verify CI index updated"
grep -q 'PATCHER_WRAPPER_LINKS_v1_BEGIN' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -q 'docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> verify rules of engagement updated"
grep -q 'PATCHER_WRAPPER_LINKS_v1_BEGIN' docs/process/rules_of_engagement.md
grep -q 'docs/process/Canonical_Patcher_Wrapper_Pattern_v1.0.md' docs/process/rules_of_engagement.md

echo "OK"
