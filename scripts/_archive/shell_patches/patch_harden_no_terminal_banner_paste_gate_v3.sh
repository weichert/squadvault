#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: harden terminal banner paste gate (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_harden_no_terminal_banner_paste_gate_v3.py"
GATE="scripts/gate_no_terminal_banner_paste_v1.sh"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> Run patcher: ${PATCHER}"
${PY} "${PATCHER}"

echo "==> Ensure gate is executable"
chmod +x "${GATE}"

echo "==> bash syntax check"
bash -n "${GATE}"
echo "OK: bash -n passed"

echo "==> Run gate once"
bash "${GATE}"
echo "OK: gate run complete"
