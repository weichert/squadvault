#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: gate_no_xtrace remove bare marker line (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_no_xtrace_remove_bare_marker_v2.py

echo "==> bash syntax check"
bash -n scripts/gate_no_xtrace_v1.sh
echo "OK"
