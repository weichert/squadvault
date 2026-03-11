#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: remove contracts gate autofill placeholder line (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

$PY scripts/_patch_docs_remove_contracts_gate_autofill_line_v1.py

echo "==> verify placeholder removed (best-effort)"
grep -n "gate_contracts_index_discoverability_v1.sh — (autofill)" docs/80_indices/ops/CI_Guardrails_Index_v1.0.md || true
echo "OK"
