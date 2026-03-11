#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add banner gate proof + prove_ci hint (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_prove_terminal_banner_gate_behavior_and_ci_hint_v3.py"
PROOF="scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> Run patcher: ${PATCHER}"
${PY} "${PATCHER}"

echo "==> Ensure proof is executable"
chmod +x "${PROOF}"

echo "==> bash syntax check"
bash -n "${PROOF}"
bash -n scripts/prove_ci.sh
echo "OK: bash -n passed"

echo "==> Run proof once (only if repo is clean)"
if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "WARN: repo is not clean (expected while patch artifacts are uncommitted); skipping proof run."
  echo "      Commit changes, then run: bash ${PROOF}"
  exit 0
fi

bash "${PROOF}"
echo "OK"
