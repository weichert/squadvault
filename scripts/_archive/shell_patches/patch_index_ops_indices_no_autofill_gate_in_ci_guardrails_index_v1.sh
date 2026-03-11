#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index ops indices no-autofill gate in CI Guardrails index (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_index_ops_indices_no_autofill_gate_in_ci_guardrails_index_v1.py

echo "==> verify bounded markers exist"
grep -nF '<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF '<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> verify bullet exists"
grep -nF 'scripts/gate_ops_indices_no_autofill_placeholders_v1.sh' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> docs integrity (v2)"
bash scripts/gate_docs_integrity_v2.sh

echo "OK"
