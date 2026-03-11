#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: allowlist docs-fill wrapper for idempotence gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_allowlist_patch_wrapper_docs_fill_ci_guardrails_autofill_descriptions_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "==> verify wrapper present"
grep -nF 'scripts/patch_docs_fill_ci_guardrails_autofill_descriptions_v1.sh' scripts/gate_patch_wrapper_idempotence_allowlist_v1.sh

echo "OK"
