#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire allowlist patchers insert-sorted gate into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_wire_gate_allowlist_patchers_insert_sorted_into_prove_ci_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "==> verify invocation present"
grep -nF 'bash scripts/gate_allowlist_patchers_must_insert_sorted_v1.sh' scripts/prove_ci.sh

echo "OK"
