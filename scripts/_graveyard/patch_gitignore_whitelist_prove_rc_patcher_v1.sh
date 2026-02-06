#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: .gitignore whitelist prove RC patcher (v1) ==="
cd "$(git rev-parse --show-toplevel)"

./scripts/py scripts/_patch_gitignore_whitelist_prove_rc_patcher_v1.py

echo "==> prove ignore result"
git check-ignore -v scripts/_patch_fix_prove_rc_approved_by_v5.py || echo "OK: not ignored"

echo "==> show remaining _patch_*.py ignore globs"
grep -n '^scripts/_patch_\*\.py$' .gitignore || true

echo "OK"
