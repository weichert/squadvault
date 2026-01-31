#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add filesystem ordering determinism gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python3}"
if ! command -v "${python}" >/dev/null 2>&1; then
  python="python"
fi

"${python}" scripts/_patch_add_filesystem_ordering_gate_v1.py

echo "==> bash -n"
bash -n scripts/check_filesystem_ordering_determinism.sh

echo "OK"
