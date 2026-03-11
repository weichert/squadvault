#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: deprecate docs mutation guardrail v1 + index v2 gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_deprecate_docs_mutation_guardrail_v1_and_index_v2_gate_v1.py
"${PY}" scripts/_patch_deprecate_docs_mutation_guardrail_v1_and_index_v2_gate_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_docs_mutation_guardrail_v1.sh
bash -n scripts/patch_deprecate_docs_mutation_guardrail_v1_and_index_v2_gate_v1.sh

echo "==> verify index needles present"
grep -nF "SV_DOCS_MUTATION_GUARDRAIL_GATE: v2" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF "scripts/gate_docs_mutation_guardrail_v2.sh" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
