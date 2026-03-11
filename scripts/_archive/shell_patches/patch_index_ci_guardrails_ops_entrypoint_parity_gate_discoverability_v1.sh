#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index CI guardrails ops entrypoint parity gate discoverability (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_index_ci_guardrails_ops_entrypoint_parity_gate_discoverability_v1.py

echo "==> verify markers exist"
grep -nF '<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_BEGIN -->' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF '<!-- SV_CI_GUARDRAILS_ENTRYPOINTS_v1_END -->' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "==> verify new gate bullet exists"
grep -nF 'scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
