#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci add no-untracked patch artifacts gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

PATCHER="scripts/_patch_prove_ci_add_no_untracked_patch_artifacts_gate_v1.py"
GATE="scripts/gate_no_untracked_patch_artifacts_v1.sh"
PROVE="scripts/prove_ci.sh"

echo "==> Run patcher"
${PY} "${PATCHER}"

echo "==> Ensure gate is executable"
chmod +x "${GATE}"

echo "==> Bash syntax check"
bash -n "${GATE}"
bash -n "${PROVE}"
echo "OK"

echo "==> Run gate standalone"
bash "${GATE}"

echo "==> Verify prove_ci invokes the gate"
grep -nE 'gate_no_untracked_patch_artifacts_v1\.sh' "${PROVE}" >/dev/null
echo "OK"

echo "=== Patch complete (v1) ==="
