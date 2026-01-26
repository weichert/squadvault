#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Apply Lock E final state (Rivalry Chronicle approval pipeline) ==="
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

run() {
  local p="$1"
  if [[ ! -f "$p" ]]; then
    echo "ERROR: expected patch wrapper not found: $p" >&2
    exit 2
  fi
  echo
  echo "==> Running: $(basename "$p")"
  "$p"
}

# Canonical final wrappers (keep these as the single source of truth).
run "${repo_root}/scripts/patch_recap_py_add_approve_rivalry_chronicle_approved_at_utc_v1.sh"
run "${repo_root}/scripts/patch_recap_py_forward_approve_rivalry_chronicle_approved_at_utc_v2.sh"
run "${repo_root}/scripts/patch_rivalry_chronicle_approve_lock_e_v11_plumb_args_approved_at_utc_into_request.sh"
run "${repo_root}/scripts/patch_core_recap_artifacts_approve_add_approved_at_utc_v1.sh"
run "${repo_root}/scripts/patch_core_recap_artifacts_force_set_approved_at_v3c.sh"

echo
echo "=== Sanity: py_compile ==="
python -m py_compile \
  "${repo_root}/scripts/recap.py" \
  "${repo_root}/src/squadvault/consumers/rivalry_chronicle_approve_v1.py" \
  "${repo_root}/src/squadvault/core/recaps/recap_artifacts.py"

echo
echo "=== Sanity: tests (Lock E idempotency) ==="
pytest -q "${repo_root}/Tests/test_rivalry_chronicle_approve_idempotency_v1.py" -q

echo
echo "OK: Lock E final state applied and verified."
