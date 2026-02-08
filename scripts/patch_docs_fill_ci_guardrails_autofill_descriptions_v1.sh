#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fill CI Guardrails ops index autofill descriptions (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_docs_fill_ci_guardrails_autofill_descriptions_v1.py

echo "==> verify no autofill placeholders remain"
grep -nF '— (autofill) describe gate purpose' docs/80_indices/ops/CI_Guardrails_Index_v1.0.md && {
  echo "ERROR: autofill placeholder still present; refuse" >&2
  exit 1
} || true

echo "==> run parity gate (should still pass)"
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> docs integrity (v2)"
bash scripts/gate_docs_integrity_v2.sh

echo "OK"
