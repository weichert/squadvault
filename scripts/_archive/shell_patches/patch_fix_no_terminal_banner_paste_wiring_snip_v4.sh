#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix terminal-banner gate wiring SNIP (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_no_terminal_banner_paste_wiring_snip_v4.py

echo "==> grep: show SNIP"
grep -n "SNIP =" scripts/_patch_wire_no_terminal_banner_paste_gate_into_prove_ci_v2.py

echo "==> py_compile"
${PY} -m py_compile scripts/_patch_wire_no_terminal_banner_paste_gate_into_prove_ci_v2.py

echo "OK"
