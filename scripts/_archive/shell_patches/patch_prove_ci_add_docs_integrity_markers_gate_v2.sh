#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add docs integrity markers gate (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_prove_ci_add_docs_integrity_markers_gate_v2.py
"${PY}" scripts/_patch_prove_ci_add_docs_integrity_markers_gate_v2.py

chmod +x scripts/gate_docs_integrity_markers_v2.sh

echo "==> bash syntax check"
bash -n scripts/gate_docs_integrity_markers_v2.sh
bash -n scripts/patch_prove_ci_add_docs_integrity_markers_gate_v2.sh
bash -n scripts/prove_ci.sh

echo "==> run new gate directly"
bash scripts/gate_docs_integrity_markers_v2.sh

echo "==> run prove_ci (expected DIRTY until commit)"
bash scripts/prove_ci.sh || true

echo "OK (pre-commit proof may fail cleanliness; commit next)."
