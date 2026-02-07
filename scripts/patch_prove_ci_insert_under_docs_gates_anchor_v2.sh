#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci insert a doc/index gate under docs_gates anchor (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

: "${SV_DOCS_GATES_INSERT_LABEL:?missing SV_DOCS_GATES_INSERT_LABEL}"
: "${SV_DOCS_GATES_INSERT_PATH:?missing SV_DOCS_GATES_INSERT_PATH}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_insert_under_docs_gates_anchor_v2.py

echo "==> Verify: prove_ci contains an invocation of the requested gate (by basename)"
gate_base="$(basename "${SV_DOCS_GATES_INSERT_PATH}")"
grep -nF "${gate_base}" scripts/prove_ci.sh >/dev/null

echo "==> Verify: reject accidental double 'scripts/scripts/'"
BAD="bash scripts/""scripts/"; if grep -nF "${BAD}" scripts/prove_ci.sh >/dev/null; then
  echo "ERROR: detected forbidden double scripts prefix in scripts/prove_ci.sh"
  exit 1
fi

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_insert_under_docs_gates_anchor_v2.sh

echo "OK"
