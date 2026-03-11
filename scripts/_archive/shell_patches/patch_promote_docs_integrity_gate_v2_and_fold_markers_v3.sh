#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: promote docs integrity gate v2 + fold markers gate (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_promote_docs_integrity_gate_v2_and_fold_markers_v3.py
"${PY}" scripts/_patch_promote_docs_integrity_gate_v2_and_fold_markers_v3.py

chmod +x scripts/gate_docs_integrity_v2.sh

echo "==> bash syntax check"
bash -n scripts/gate_docs_integrity_v2.sh
bash -n scripts/patch_promote_docs_integrity_gate_v2_and_fold_markers_v3.sh
bash -n scripts/prove_ci.sh

echo "==> confirm markers block removed"
grep -nF "SV_GATE: docs_integrity_markers (v2)" scripts/prove_ci.sh && exit 1 || true

echo "==> run new gate directly"
bash scripts/gate_docs_integrity_v2.sh

echo "==> run prove_ci (expected DIRTY until commit)"
bash scripts/prove_ci.sh || true

echo "OK (pre-commit proof may fail cleanliness; commit next)."
