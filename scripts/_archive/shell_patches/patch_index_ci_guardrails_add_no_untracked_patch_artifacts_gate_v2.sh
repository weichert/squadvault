#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: CI guardrails index add no-untracked patch artifacts gate (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_index_ci_guardrails_add_no_untracked_patch_artifacts_gate_v2.py"
DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

echo "==> Run patcher"
${PY} "${PATCHER}"

echo "==> Verify bullet exists"
grep -nE 'gate_no_untracked_patch_artifacts_v1\.sh' "${DOC}" >/dev/null
echo "OK"

echo "=== Patch complete (v2) ==="
