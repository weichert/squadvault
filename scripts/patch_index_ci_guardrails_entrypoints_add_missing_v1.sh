#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index missing CI guardrails entrypoints for parity (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_index_ci_guardrails_entrypoints_add_missing_v1.py

echo "==> py_compile"
"${PY}" -m py_compile scripts/_patch_index_ci_guardrails_entrypoints_add_missing_v1.py

echo "==> verify bullets present (bounded index)"
grep -nF "scripts/gate_cwd_independence_shims_v1.sh" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -nF "scripts/gate_no_xtrace_v1.sh" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md

echo "OK"
