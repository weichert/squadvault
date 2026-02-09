#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: make prove_golden_path CWD-independent (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_golden_path_cwd_independent_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> sanity: prove_golden_path must not use git rev-parse for repo root"
if grep -n "git rev-parse --show-toplevel" scripts/prove_golden_path.sh >/dev/null 2>&1; then
  echo "ERROR: rev-parse still present in scripts/prove_golden_path.sh" >&2
  grep -n "git rev-parse --show-toplevel" scripts/prove_golden_path.sh >&2
  exit 1
fi

echo "OK"
