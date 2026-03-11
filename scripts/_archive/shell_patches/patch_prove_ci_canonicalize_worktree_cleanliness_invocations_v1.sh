#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: canonicalize worktree cleanliness gate invocations in prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_canonicalize_worktree_cleanliness_invocations_v1.py

echo "==> py_compile"
"${PY}" -m py_compile scripts/_patch_prove_ci_canonicalize_worktree_cleanliness_invocations_v1.py

echo "==> verify canonical invocation form"
grep -nE 'bash scripts/gate_worktree_cleanliness_v1\.sh' scripts/prove_ci.sh

echo "OK"
