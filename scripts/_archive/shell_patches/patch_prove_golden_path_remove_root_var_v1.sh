#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: remove ROOT var usage from prove_golden_path (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_golden_path_remove_root_var_v1.py

echo "==> sanity: no ROOT references remain"
if grep -nE '\bROOT\b' scripts/prove_golden_path.sh >/dev/null 2>&1; then
  echo "ERROR: ROOT still referenced in scripts/prove_golden_path.sh" >&2
  grep -nE '\bROOT\b' scripts/prove_golden_path.sh >&2
  exit 1
fi

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "OK"
