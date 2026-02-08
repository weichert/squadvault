#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add DESC for no-obsolete allowlist gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} -m py_compile scripts/_patch_fix_ci_guardrails_autofill_desc_add_no_obsolete_allowlist_gate_v1.py
${PY} scripts/_patch_fix_ci_guardrails_autofill_desc_add_no_obsolete_allowlist_gate_v1.py

echo "==> run autofill wrapper (should now succeed)"
bash scripts/patch_docs_fill_ci_guardrails_autofill_descriptions_v1.sh

echo "==> bash -n prove_ci"
bash -n scripts/prove_ci.sh

echo "OK"
