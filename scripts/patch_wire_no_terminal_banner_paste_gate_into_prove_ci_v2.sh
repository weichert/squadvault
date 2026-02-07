#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: wire no-terminal-banner-paste gate into prove_ci (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_wire_no_terminal_banner_paste_gate_into_prove_ci_v2.py

echo "==> bash -n prove_ci"
bash -n scripts/prove_ci.sh

echo "==> grep: confirm wiring"
grep -n "gate_no_terminal_banner_paste_v1.sh" scripts/prove_ci.sh

echo "OK"
