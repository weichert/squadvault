#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add DESC for proof registry exactness gate to CI guardrails autofill (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_fix_ci_guardrails_autofill_desc_add_proof_registry_exactness_gate_v4.py

echo "==> py_compile target"
$PY -m py_compile scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py

echo "OK"
