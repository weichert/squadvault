#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: bulk-index missing CI guardrails entrypoints from prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_bulk_index_missing_ci_guardrails_entrypoints_from_prove_ci_v1.py

echo "==> verify bounded markers exist"
grep -nF '<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF '<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> spot-check: ensure newly-added gates are present"
grep -nF 'scripts/gate_docs_integrity_v2.sh' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF 'scripts/gate_proof_suite_completeness_v1.sh' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF 'scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
