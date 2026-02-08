#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: ops index add terminal banner gate entry (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_docs_ops_index_add_terminal_banner_gate_entry_v1.py"
DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> Run patcher: ${PATCHER}"
${PY} "${PATCHER}"

echo "==> Sanity: doc exists"
test -f "${DOC}"

echo "OK"
