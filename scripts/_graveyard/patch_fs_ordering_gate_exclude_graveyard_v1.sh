#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: fs ordering gate excludes scripts/_graveyard (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
"${python}" scripts/_patch_fs_ordering_gate_exclude_graveyard_v1.py

echo "==> bash syntax check"
bash -n scripts/check_filesystem_ordering_determinism.sh

echo "OK"
