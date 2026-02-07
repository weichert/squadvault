#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add docs mutation guardrail gate + wire into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_prove_ci_add_docs_mutation_guardrail_gate_v1.py
"${PY}" scripts/_patch_prove_ci_add_docs_mutation_guardrail_gate_v1.py

# Ensure new gate is executable
chmod +x scripts/gate_docs_mutation_guardrail_v1.sh

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/gate_docs_mutation_guardrail_v1.sh
bash -n scripts/patch_prove_ci_add_docs_mutation_guardrail_gate_v1.sh

echo "==> run new gate directly"
bash scripts/gate_docs_mutation_guardrail_v1.sh

echo "==> run prove_ci"
bash scripts/prove_ci.sh

echo "OK"
