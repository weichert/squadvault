#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci upgrade no double scripts prefix gate to v2 (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

# Ensure v2 gate exists
test -f scripts/gate_no_double_scripts_prefix_v2.sh

"${PY}" scripts/_patch_prove_ci_upgrade_no_double_scripts_prefix_gate_v2.py

echo "==> Verify: prove_ci references v2 gate"
grep -nF "bash scripts/gate_no_double_scripts_prefix_v2.sh" scripts/prove_ci.sh >/dev/null
grep -nF 'echo "==> Gate: no double scripts prefix (v2)"' scripts/prove_ci.sh >/dev/null

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_upgrade_no_double_scripts_prefix_gate_v2.sh

echo "OK"
