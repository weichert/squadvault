#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire patcher no-ops when prove_ci already canonical (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_wire_patcher_worktree_cleanliness_noop_if_canonical_v1.py

echo "==> py_compile"
"${PY}" -m py_compile scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py
"${PY}" -m py_compile scripts/_patch_wire_patcher_worktree_cleanliness_noop_if_canonical_v1.py

echo "OK"
