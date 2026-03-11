#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: restore docs integrity proof surface + keep docs_integrity_v2 gate-only (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_restore_docs_integrity_proof_surface_v1.py
"${PY}" scripts/_patch_restore_docs_integrity_proof_surface_v1.py

chmod +x scripts/gate_docs_integrity_v2.sh

echo "==> bash syntax check"
bash -n scripts/gate_docs_integrity_v2.sh
bash -n scripts/prove_ci.sh
bash -n scripts/patch_restore_docs_integrity_proof_surface_v1.sh

echo "==> confirm prove_ci directly invokes prove_docs_integrity_v1"
grep -nF "bash scripts/prove_docs_integrity_v1.sh" scripts/prove_ci.sh

echo "==> confirm gate_docs_integrity_v2 does NOT invoke prove_docs_integrity_v1"
grep -nF "prove_docs_integrity_v1.sh" scripts/gate_docs_integrity_v2.sh && exit 1 || true

echo "==> run prove_ci (expected DIRTY until commit)"
bash scripts/prove_ci.sh || true

echo "OK (pre-commit proof may fail cleanliness; commit next)."
