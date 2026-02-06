#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add gate_no_xtrace_v1.sh (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_add_gate_no_xtrace_v1.py

echo "==> bash syntax check"
bash -n scripts/gate_no_xtrace_v1.sh
echo "OK"
