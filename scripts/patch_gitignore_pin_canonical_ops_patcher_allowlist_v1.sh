#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: .gitignore pin canonical ops patcher allowlist (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
"${python}" scripts/_patch_gitignore_pin_canonical_ops_patcher_allowlist_v1.py

echo "OK"
