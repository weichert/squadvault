#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs mutation guardrail v2 harden + dedupe CI index (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_docs_mutation_guardrail_gate_v2_harden_and_dedupe_v1.py
"${PY}" scripts/_patch_docs_mutation_guardrail_gate_v2_harden_and_dedupe_v1.py

chmod +x scripts/gate_docs_mutation_guardrail_v2.sh

echo "==> bash syntax check"
bash -n scripts/gate_docs_mutation_guardrail_v2.sh
bash -n scripts/patch_docs_mutation_guardrail_gate_v2_harden_and_dedupe_v1.sh
bash -n scripts/prove_ci.sh

echo "==> run new gate directly"
bash scripts/gate_docs_mutation_guardrail_v2.sh

echo "==> run prove_ci (expected DIRTY until commit)"
bash scripts/prove_ci.sh || true

echo "OK (pre-commit proof may fail cleanliness; commit next)."
