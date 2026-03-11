#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: add DESC for Rivalry Chronicle output contract gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_docs_add_desc_rivalry_chronicle_output_contract_gate_v1.py

echo "==> py_compile target patcher"
$PY -m py_compile scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py
echo "OK"
