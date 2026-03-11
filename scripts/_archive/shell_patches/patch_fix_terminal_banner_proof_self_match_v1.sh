#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix terminal banner proof self-match (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_fix_terminal_banner_proof_self_match_v1.py"
PROOF="scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> Run patcher: ${PATCHER}"
${PY} "${PATCHER}"

echo "==> Ensure scripts are executable"
chmod +x "${PROOF}"

echo "==> bash syntax check"
bash -n "${PROOF}"
bash -n scripts/prove_ci.sh
echo "OK: bash -n passed"

echo "==> Run banner gate"
bash scripts/gate_no_terminal_banner_paste_v1.sh

echo "==> Run proof (requires clean repo)"
if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "WARN: repo is not clean (expected while patch artifacts are uncommitted); skipping proof run."
  echo "      Commit changes, then run: bash ${PROOF}"
  exit 0
fi

bash "${PROOF}"
echo "OK"
