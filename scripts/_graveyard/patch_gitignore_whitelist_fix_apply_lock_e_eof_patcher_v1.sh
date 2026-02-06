#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: .gitignore whitelist (apply Lock E EOF fix patcher) v1 ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

./scripts/py scripts/_patch_gitignore_whitelist_fix_apply_lock_e_eof_patcher_v1.py

echo
echo "== Verify: git check-ignore =="
git check-ignore -v scripts/_patch_fix_apply_lock_e_wrapper_unexpected_eof_v1.py || echo "OK: not ignored"
