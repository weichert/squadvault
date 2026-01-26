#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: Lock E collapse remaining wrapper scripts into single apply wrapper (v1) ==="

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

apply="scripts/patch_apply_lock_e_final_state.sh"
if [[ ! -f "${apply}" ]]; then
  echo "ERROR: expected ${apply} to exist"
  exit 2
fi

# The canonical python patchers we want the apply wrapper to call directly.
py_patchers=(
  "scripts/_patch_recap_py_add_approve_rivalry_chronicle_approved_at_utc_v1.py"
  "scripts/_patch_recap_py_forward_approve_rivalry_chronicle_approved_at_utc_v2.py"
  "scripts/_patch_rivalry_chronicle_approve_lock_e_v11_plumb_args_approved_at_utc_into_request.py"
  "scripts/_patch_core_recap_artifacts_approve_add_approved_at_utc_v1.py"
  "scripts/_patch_core_recap_artifacts_force_set_approved_at_v3c.py"
)

echo "==> Sanity: python patchers exist"
missing=0
for f in "${py_patchers[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "missing: $f"
    missing=1
  fi
done
if [[ "${missing}" -ne 0 ]]; then
  echo "ERROR: missing python patchers; refusing."
  exit 2
fi
echo "OK: all python patchers present."

# Wrapper scripts we intend to delete after we rewrite the apply wrapper.
wrappers_to_remove=(
  "scripts/patch_recap_py_add_approve_rivalry_chronicle_approved_at_utc_v1.sh"
  "scripts/patch_recap_py_forward_approve_rivalry_chronicle_approved_at_utc_v2.sh"
  "scripts/patch_rivalry_chronicle_approve_lock_e_v11_plumb_args_approved_at_utc_into_request.sh"
  "scripts/patch_core_recap_artifacts_approve_add_approved_at_utc_v1.sh"
  "scripts/patch_core_recap_artifacts_force_set_approved_at_v3c.sh"
)

# Rewrite apply wrapper to call python patchers directly (idempotent).
marker="LOCK_E_APPLY_WRAPPER_CALLS_PY_PATCHERS_V1"
if grep -q "${marker}" "${apply}"; then
  echo "OK: apply wrapper already rewritten; skipping rewrite."
else
  echo "==> Rewriting ${apply} to call python patchers directly"
  cat > "${apply}" <<'EOF'
#!/usr/bin/env bash
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
EOF
  chmod +x "${apply}"
  echo "OK: rewritten ${apply}"
fi

echo
echo "==> Removing superseded wrapper scripts (idempotent)"
deleted=0
for w in "${wrappers_to_remove[@]}"; do
  if [[ -f "${w}" ]]; then
    rm -f "${w}"
    echo "deleted: ${w}"
    deleted=$((deleted+1))
  else
    echo "missing (ok): ${w}"
  fi
done

echo
echo "==> Final check: run apply wrapper"
"${apply}"

echo
echo "OK: collapse complete. deleted=${deleted}"
