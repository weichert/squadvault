#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire patcher uses direct worktree cleanliness gate invocation (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_wire_patcher_worktree_cleanliness_invocation_style_v1.py

echo "==> py_compile"
"${PY}" -m py_compile scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py

echo "==> verify pattern removed"
if grep -n "bash scripts/gate_worktree_cleanliness_v1.sh" scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py; then
  echo "ERROR: wire patcher still contains bash+scripts invocation" >&2
  exit 1
fi

echo "OK"
