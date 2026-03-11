#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index worktree cleanliness gate discoverability (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_index_worktree_cleanliness_gate_discoverability_v1.py
echo "==> verify marker + bullet present"
grep -n "SV_CI_WORKTREE_CLEANLINESS" -n docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
grep -n "gate_worktree_cleanliness_v1.sh" -n docs/80_indices/ops/CI_Guardrails_Index_v1.0.md
echo "OK"
