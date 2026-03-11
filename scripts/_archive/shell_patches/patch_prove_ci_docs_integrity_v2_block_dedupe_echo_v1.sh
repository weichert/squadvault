#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: dedupe docs integrity gate (v2) banner in prove_ci block (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" -m py_compile scripts/_patch_prove_ci_docs_integrity_v2_block_dedupe_echo_v1.py
"${PY}" scripts/_patch_prove_ci_docs_integrity_v2_block_dedupe_echo_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_docs_integrity_v2_block_dedupe_echo_v1.sh

echo "==> confirm prove_ci does not echo docs integrity v2 banner (gate owns banner)"
grep -nF 'echo "==> Docs integrity gate (v2)"' scripts/prove_ci.sh && exit 1 || true

echo "==> run prove_ci (expected DIRTY until commit)"
bash scripts/prove_ci.sh || true

echo "OK (pre-commit proof may fail cleanliness; commit next)."
