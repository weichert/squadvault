#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: gate_no_untracked_patch_artifacts fix grep regex (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_gate_no_untracked_patch_artifacts_fix_grep_v2.py"
GATE="scripts/gate_no_untracked_patch_artifacts_v1.sh"

echo "==> Run patcher"
${PY} "${PATCHER}"

echo "==> Bash syntax check"
bash -n "${GATE}"
echo "OK"

echo "==> Show hits line (for sanity)"
grep -nE '^[[:space:]]*hits=' "${GATE}" || true

echo "==> Run gate"
bash "${GATE}"

echo "=== Patch complete (v2) ==="
