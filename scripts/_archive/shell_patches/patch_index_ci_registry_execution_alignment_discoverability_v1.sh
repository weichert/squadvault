#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index CI registry→execution alignment gate discoverability (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> py_compile patcher"
"${PY}" -m py_compile scripts/_patch_index_ci_registry_execution_alignment_discoverability_v1.py

echo "==> run patcher"
"${PY}" scripts/_patch_index_ci_registry_execution_alignment_discoverability_v1.py

echo "==> verify marker + bullet present exactly once"
DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

grep -nF '<!-- SV_CI_REGISTRY_EXECUTION_ALIGNMENT: v1 -->' "${DOC}"
grep -nF 'scripts/gate_ci_registry_execution_alignment_v1.sh — CI Registry → Execution Alignment Gate (v1)' "${DOC}"

m_count="$(grep -cF '<!-- SV_CI_REGISTRY_EXECUTION_ALIGNMENT: v1 -->' "${DOC}" || true)"
b_count="$(grep -cF 'scripts/gate_ci_registry_execution_alignment_v1.sh — CI Registry → Execution Alignment Gate (v1)' "${DOC}" || true)"

if [[ "${m_count}" -ne 1 ]]; then
  echo "ERROR: marker count != 1 (found ${m_count})" >&2
  exit 1
fi
if [[ "${b_count}" -ne 1 ]]; then
  echo "ERROR: bullet count != 1 (found ${b_count})" >&2
  exit 1
fi

echo "OK"
