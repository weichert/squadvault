#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add guardrails autofill description for proof registry excludes gates (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_desc_map_add_proof_registry_excludes_gates_v4.py

echo "==> python compile"
${PY} -m py_compile scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py

echo "OK"
