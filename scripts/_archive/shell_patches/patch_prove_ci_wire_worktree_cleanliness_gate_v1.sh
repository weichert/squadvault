#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire worktree cleanliness gate into prove_ci (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_ci_wire_worktree_cleanliness_gate_v1.py
echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
echo "==> verify gate referenced"
grep -n "gate_worktree_cleanliness_v1.sh" scripts/prove_ci.sh
echo "OK"
