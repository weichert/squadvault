#!/usr/bin/env bash
set -euo pipefail

echo "=== Bundle Patch: fix CI pytest DB source follow-ups (v2) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/patch_fix_future_import_order_for_os_v1.sh"
"$repo_root/scripts/patch_gitignore_unignore_new_patchers_ci_db_fix_v2.sh"

echo "==> bash -n (new wrappers)"
bash -n "$repo_root/scripts/patch_fix_ci_pytest_db_source_v2.sh"
bash -n "$repo_root/scripts/patch_fix_future_import_order_for_os_v1.sh"
bash -n "$repo_root/scripts/patch_gitignore_unignore_new_patchers_ci_db_fix_v2.sh"

echo "==> Shim compliance"
"$repo_root/scripts/check_shims_compliance.sh"

echo "==> Optional: run prove_ci.sh ONLY if repo is clean"
if git -C "$repo_root" diff --quiet && test -z "$(git -C "$repo_root" status --porcelain=v1)"; then
  "$repo_root/scripts/verify_ci_after_db_fix_v1.sh"
else
  echo "NOTE: repo is dirty; skipping prove_ci.sh (by design)."
  echo "      After commit, run: ./scripts/verify_ci_after_db_fix_v1.sh"
fi

echo "OK: bundle patch complete (v2)"
