#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: docs index entry for proof suite completeness gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

: "${SV_CI_INDEX_DOC:?SV_CI_INDEX_DOC must be set}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

SV_CI_INDEX_DOC="${SV_CI_INDEX_DOC}" "${PY}" scripts/_patch_docs_add_proof_suite_completeness_gate_index_v1.py

echo "==> verify markers"
grep -n 'PROOF_SUITE_COMPLETENESS_GATE_v1_' "${SV_CI_INDEX_DOC}"

echo "OK"
