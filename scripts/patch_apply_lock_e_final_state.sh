#!/usr/bin/env bash
# CANONICAL ENTRYPOINT — DO NOT WRAP
# All Lock E patchers are invoked directly here.
# If Lock E changes, update python patchers and this file only.
set -euo pipefail

echo "=== Patch: Apply Lock E final state (Rivalry Chronicle approval pipeline) ==="

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

run_py() {
  local py="$1"
  echo
  echo "==> Running: ${py}"
  "${repo_root}/scripts/py" "${repo_root}/${py}"
}

# LOCK_E_APPLY_WRAPPER_CALLS_PY_PATCHERS_V1
run_py "scripts/_patch_recap_py_add_approve_rivalry_chronicle_approved_at_utc_v1.py"
run_py "scripts/_patch_recap_py_forward_approve_rivalry_chronicle_approved_at_utc_v2.py"
run_py "scripts/_patch_rivalry_chronicle_approve_lock_e_v11_plumb_args_approved_at_utc_into_request.py"
run_py "scripts/_patch_core_recap_artifacts_approve_add_approved_at_utc_v1.py"
run_py "scripts/_patch_core_recap_artifacts_force_set_approved_at_v3c.py"

echo
echo "=== Sanity: py_compile ==="
python -m py_compile \
  src/squadvault/consumers/rivalry_chronicle_approve_v1.py \
  scripts/recap.py \
  src/squadvault/core/recaps/recap_artifacts.py

echo
echo "=== Sanity: tests (Lock E idempotency) ==="
pytest -q Tests/test_rivalry_chronicle_approve_idempotency_v1.py -q

echo
echo "OK: Lock E final state applied and verified."
# --- Optional sanity probe (requires sqlite3 + SV_DB_PATH) ---
if command -v sqlite3 >/dev/null 2>&1 && [[ -n "${SV_DB_PATH:-}" ]]; then
  echo
  echo "=== Sanity: latest APPROVED RIVALRY_CHRONICLE_V1 has approved_at set ==="
  sqlite3 "${SV_DB_PATH}" "
    SELECT week_index, version, state, approved_at, approved_by
    FROM recap_artifacts
    WHERE artifact_type='RIVALRY_CHRONICLE_V1'
      AND state='APPROVED'
    ORDER BY week_index DESC, version DESC
    LIMIT 1;
  " || true
fi

# LOCK_E_APPLY_WRAPPER_TINY_POLISH_V1
