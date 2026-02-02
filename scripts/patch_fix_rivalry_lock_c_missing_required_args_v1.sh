#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Rivalry Chronicle Lock C — add required db_path + rendered_text ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

./scripts/py scripts/_patch_fix_rivalry_lock_c_missing_required_args_v1.py
