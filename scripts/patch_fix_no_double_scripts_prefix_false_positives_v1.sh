#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix no-double-scripts-prefix false positives (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_fix_no_double_scripts_prefix_false_positives_v1.py

echo "==> Verify: v2 gate no longer contains literal scripts/scripts/"
if grep -nF "scripts/scripts/" scripts/gate_no_double_scripts_prefix_v2.sh >/dev/null; then
  echo "ERROR: v2 gate still contains literal scripts/scripts/"
  grep -nF "scripts/scripts/" scripts/gate_no_double_scripts_prefix_v2.sh || true
  exit 1
fi

echo "==> bash syntax check"
bash -n scripts/gate_no_double_scripts_prefix_v2.sh
bash -n scripts/gate_no_double_scripts_prefix_v1.sh
bash -n scripts/patch_prove_ci_insert_under_docs_gates_anchor_v2.sh
bash -n scripts/patch_fix_no_double_scripts_prefix_false_positives_v1.sh

echo "OK"
