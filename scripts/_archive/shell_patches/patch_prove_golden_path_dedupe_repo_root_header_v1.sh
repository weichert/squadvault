#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: dedupe prove_golden_path SCRIPT_DIR/REPO_ROOT header (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_prove_golden_path_dedupe_repo_root_header_v1.py

echo "==> bash syntax check"
bash -n scripts/prove_golden_path.sh

echo "==> sanity: only one SCRIPT_DIR header assignment remains"
cnt="$(grep -c 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE\[0\]}"' scripts/prove_golden_path.sh || true)"
if [[ "${cnt}" != "1" ]]; then
  echo "ERROR: expected exactly 1 SCRIPT_DIR header assignment, got ${cnt}" >&2
  grep -n 'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE' scripts/prove_golden_path.sh >&2 || true
  exit 1
fi

echo "OK"
