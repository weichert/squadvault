#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix prove_ci marker for terminal-banner gate (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_no_terminal_banner_paste_prove_ci_marker_v3.py

echo "==> bash -n prove_ci"
bash -n scripts/prove_ci.sh

echo "==> grep: confirm echo marker"
grep -n 'Gate: no pasted terminal banners in scripts/' scripts/prove_ci.sh

echo "OK"
