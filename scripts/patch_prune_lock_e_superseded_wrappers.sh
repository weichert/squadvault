#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Prune superseded Lock E wrappers ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

keep=(
  "scripts/patch_apply_lock_e_final_state.sh"
  "scripts/patch_core_recap_artifacts_approve_add_approved_at_utc_v1.sh"
  "scripts/patch_core_recap_artifacts_force_set_approved_at_v3c.sh"
  "scripts/patch_recap_py_add_approve_rivalry_chronicle_approved_at_utc_v1.sh"
  "scripts/patch_recap_py_forward_approve_rivalry_chronicle_approved_at_utc_v2.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v11_plumb_args_approved_at_utc_into_request.sh"
)

prune=(
  # Rivalry Chronicle approve: superseded iterations
  "scripts/patch_rivalry_chronicle_approve_lock_e_v2.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v3.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v4_fix_spacing.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v5b_fix_callsite_indent.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v6_db_path_compat.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v7_idempotent_if_approved.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v8_make_approved_at_utc_optional.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v9_dataclass_default_order_fix.sh"

  # Core approve approved_at: superseded / dead-end variants
  "scripts/patch_core_recap_artifacts_approve_force_set_approved_at_v2.sh"
  "scripts/patch_core_recap_artifacts_approve_force_set_approved_at_v2b.sh"
  "scripts/patch_core_recap_artifacts_force_set_approved_at_v3.sh"
  "scripts/patch_core_recap_artifacts_force_set_approved_at_v3b.sh"
)

echo
echo "==> Sanity: required keepers exist"
for f in "${keep[@]}"; do
  if [[ ! -f "${repo_root}/${f}" ]]; then
    echo "ERROR: missing required keeper: ${f}"
    exit 1
  fi
done
echo "OK: keepers present."

echo
echo "==> Prune: deleting superseded wrappers (idempotent)"
deleted=0
missing=0
for f in "${prune[@]}"; do
  if [[ -f "${repo_root}/${f}" ]]; then
    rm -f -- "${repo_root}/${f}"
    echo "deleted: ${f}"
    deleted=$((deleted+1))
  else
    echo "missing (ok): ${f}"
    missing=$((missing+1))
  fi
done

echo
echo "==> Final check: list remaining Lock E wrappers"
ls -1 "${repo_root}"/scripts/patch_rivalry_chronicle_approve_lock_e_v*.sh 2>/dev/null \
  | sed 's|^| - |' || true

echo
echo "OK: prune complete. deleted=${deleted} missing=${missing}"
