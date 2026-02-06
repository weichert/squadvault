#!/usr/bin/env bash
set -euo pipefail

echo "=== Bundle Patch: CI recap_runs seed + export placement (v5) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

"$repo_root/scripts/patch_move_squadvault_test_db_export_after_workdb_final_v3.sh"
"$repo_root/scripts/patch_seed_recap_runs_row_in_eal_writer_boundary_test_v1.sh"
"$repo_root/scripts/patch_gitignore_unignore_new_patchers_ci_recap_runs_v5.sh"

echo "==> bash -n (new/modified wrappers)"
bash -n "$repo_root/scripts/patch_fix_ci_recap_runs_seed_v5.sh"
bash -n "$repo_root/scripts/patch_move_squadvault_test_db_export_after_workdb_final_v3.sh"
bash -n "$repo_root/scripts/patch_seed_recap_runs_row_in_eal_writer_boundary_test_v1.sh"
bash -n "$repo_root/scripts/patch_gitignore_unignore_new_patchers_ci_recap_runs_v5.sh"
bash -n "$repo_root/scripts/prove_ci.sh"

echo "==> Shim compliance"
"$repo_root/scripts/check_shims_compliance.sh"

echo "==> Optional: run prove_ci.sh ONLY if repo is clean"
if git -C "$repo_root" diff --quiet && test -z "$(git -C "$repo_root" status --porcelain=v1)"; then
  "$repo_root/scripts/verify_ci_after_db_fix_v1.sh"
else
  echo "NOTE: repo is dirty; skipping prove_ci.sh (by design)."
  echo "      After commit, run: ./scripts/verify_ci_after_db_fix_v1.sh"
fi

echo "OK: bundle patch complete (v5)"
