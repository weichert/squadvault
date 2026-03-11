#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: retire no-double-scripts-prefix v1 artifacts (shim to v2) (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_retire_no_double_scripts_prefix_v1_artifacts_v1.py

echo "==> Verify: v1 gate is now a shim to v2"
grep -nF "bash scripts/gate_no_double_scripts_prefix_v2.sh" scripts/gate_no_double_scripts_prefix_v1.sh >/dev/null

echo "==> Verify: legacy files no longer reference v1 gate path string"
if grep -nR -- "gate_no_double_scripts_prefix_v1.sh" scripts >/dev/null; then
  echo "ERROR: still found references to gate_no_double_scripts_prefix_v1.sh"
  grep -nR -- "gate_no_double_scripts_prefix_v1.sh" scripts || true
  exit 1
fi

echo "==> bash syntax check"
bash -n scripts/gate_no_double_scripts_prefix_v1.sh
bash -n scripts/patch_retire_no_double_scripts_prefix_v1_artifacts_v1.sh

echo "OK"
