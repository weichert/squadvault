#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix no-terminal-banner-paste gate impl (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_no_terminal_banner_paste_gate_impl_v2.py

echo "==> bash -n gate"
bash -n scripts/gate_no_terminal_banner_paste_v1.sh

echo "==> run gate"
bash scripts/gate_no_terminal_banner_paste_v1.sh

echo "OK"
