#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: sanitize fix-patcher to avoid banner self-match (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_fix_terminal_banner_proof_self_match_patcher_self_match_v2.py"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> Run patcher: ${PATCHER}"
${PY} "${PATCHER}"

echo "==> bash syntax check (unrelated but cheap)"
bash -n scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh
echo "OK"

echo "==> Run banner gate"
bash scripts/gate_no_terminal_banner_paste_v1.sh
echo "OK"
