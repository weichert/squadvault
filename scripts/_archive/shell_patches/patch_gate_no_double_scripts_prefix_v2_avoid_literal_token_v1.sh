#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: gate_no_double_scripts_prefix_v2 avoid literal scripts/scripts token (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_no_double_scripts_prefix_v2_avoid_literal_token_v1.py

echo "==> Verify: v2 gate contains NO literal scripts/scripts/"
if grep -nF "scripts/scripts/" scripts/gate_no_double_scripts_prefix_v2.sh >/dev/null; then
  echo "ERROR: v2 gate still contains literal scripts/scripts/"
  grep -nF "scripts/scripts/" scripts/gate_no_double_scripts_prefix_v2.sh || true
  exit 1
fi

echo "==> bash syntax check"
bash -n scripts/gate_no_double_scripts_prefix_v2.sh
bash -n scripts/patch_gate_no_double_scripts_prefix_v2_avoid_literal_token_v1.sh

echo "OK"
