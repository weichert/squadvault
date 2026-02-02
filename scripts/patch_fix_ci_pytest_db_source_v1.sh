#!/usr/bin/env bash
set -euo pipefail

echo "=== Bundle Patch: fix CI pytest DB source (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/patch_export_squadvault_test_db_in_prove_ci_v1.sh"
"$repo_root/scripts/patch_tests_use_squadvault_test_db_env_v1.sh"
"$repo_root/scripts/patch_allowlist_new_patchers_for_ci_db_fix_v1.sh"

echo "==> bash -n (new/modified wrappers)"
bash -n "$repo_root/scripts/patch_fix_ci_pytest_db_source_v1.sh"
bash -n "$repo_root/scripts/patch_export_squadvault_test_db_in_prove_ci_v1.sh"
bash -n "$repo_root/scripts/patch_tests_use_squadvault_test_db_env_v1.sh"
bash -n "$repo_root/scripts/patch_allowlist_new_patchers_for_ci_db_fix_v1.sh"
bash -n "$repo_root/scripts/verify_ci_after_db_fix_v1.sh"
bash -n "$repo_root/scripts/prove_ci.sh"

echo "==> Shim compliance"
"$repo_root/scripts/check_shims_compliance.sh"

echo "==> Optional: run prove_ci.sh ONLY if repo is clean"
if git -C "$repo_root" diff --quiet && test -z "$(git -C "$repo_root" status --porcelain=v1)"; then
  echo "OK: repo is clean; running verify wrapper"
  "$repo_root/scripts/verify_ci_after_db_fix_v1.sh"
else
  echo "NOTE: repo is dirty; skipping prove_ci.sh (by design)."
  echo "      After commit, run: ./scripts/verify_ci_after_db_fix_v1.sh"
fi

echo "OK: bundle patch complete (v1)"
