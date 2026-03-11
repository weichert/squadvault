#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci uses direct worktree cleanliness gate invocation (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_worktree_cleanliness_invocation_style_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh

echo "==> verify no 'bash scripts/gate_worktree_cleanliness_v1.sh' remains"
if grep -nE '^\s*bash scripts/gate_worktree_cleanliness_v1\.sh\b' scripts/prove_ci.sh; then
  echo "ERROR: still found bash+scripts invocation for cleanliness gate" >&2
  exit 1
fi

echo "==> verify direct invocations exist"
grep -n "scripts/gate_worktree_cleanliness_v1.sh" scripts/prove_ci.sh

echo "OK"
