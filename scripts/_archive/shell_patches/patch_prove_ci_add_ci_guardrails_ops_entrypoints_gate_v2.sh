#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci add CI Guardrails ops entrypoints gate (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_add_ci_guardrails_ops_entrypoints_gate_v2.py

echo "==> Verify: prove_ci references the new gate"
grep -nF "gate_ci_guardrails_ops_entrypoints_section_v1.sh" scripts/prove_ci.sh >/dev/null

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "OK"
