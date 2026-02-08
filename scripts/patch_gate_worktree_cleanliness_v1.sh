#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add worktree cleanliness gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_worktree_cleanliness_v1.py
chmod +x scripts/gate_worktree_cleanliness_v1.sh
echo "==> bash syntax check"
bash -n scripts/gate_worktree_cleanliness_v1.sh
echo "==> smoke"
snap="$(bash scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/gate_worktree_cleanliness_v1.sh assert "$snap" "smoke"
rm -f "$snap" || true
echo "OK"
