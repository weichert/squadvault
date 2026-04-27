#!/usr/bin/env bash

# === DETERMINISTIC EXECUTION ENVELOPE (v1) ===
# Export early so every downstream script inherits a stable baseline.
# - Locale affects sort/collation/byte ordering
# - TZ affects any incidental date/time formatting
# - PYTHONHASHSEED stabilizes hash-based ordering hazards
export LC_ALL=C
export LANG=C
export TZ=UTC
export PYTHONHASHSEED=0
# === /DETERMINISTIC EXECUTION ENVELOPE (v1) ===

# --- Temp workspace normalization (bash 3.2 safe) ---
SV_TMPDIR="${TMPDIR:-/tmp}"
SV_TMPDIR="${SV_TMPDIR%/}"
# --- /Temp workspace normalization ---

# --- Fixture immutability guard (CI) ---
# We forbid proofs from mutating committed fixtures (especially fixture DBs).
# This is a LOUD early failure to prevent masked nondeterminism.
STATEFILE="$(mktemp "${SV_TMPDIR}/squadvault_fixture_state.XXXXXX")"
if [[ -z "${STATEFILE}" ]]; then
  echo "ERROR: mktemp failed to create STATEFILE" >&2
  exit 2
fi

cleanup_fixture_state() { rm -f "${STATEFILE}" >/dev/null 2>&1 || true; }

# Collect fixture files used by CI proofs.
# - Always include the known CI DB fixture.
# - Also include any top-level sqlite fixtures (if present) to catch drift.
fixture_files=("fixtures/ci_squadvault.sqlite")
for f in fixtures/*.sqlite; do
  if [[ -f "${f}" ]]; then
    # avoid duplicate if fixtures/ci_squadvault.sqlite matches the glob
    if [[ "${f}" != "fixtures/ci_squadvault.sqlite" ]]; then
      fixture_files+=("${f}")
    fi
  fi
done

./scripts/check_fixture_immutability_ci.sh record "${STATEFILE}" "${fixture_files[@]}"
# SV_PATCH: use temp working DB copy for fixture DB (explicit, v1)
# --- Fixture DB working copy (explicit) ---
# Proofs may write to the DB; committed fixtures must remain immutable.
FIXTURE_DB="fixtures/ci_squadvault.sqlite"
WORK_DB="${FIXTURE_DB}"

if [[ -f "${FIXTURE_DB}" ]]; then
  echo "==> CI safety: using temp working DB copy (fixture remains immutable)"
  # NOTE: BSD mktemp requires template end with XXXXXX (no suffix).
  WORK_DB="$(mktemp "${SV_TMPDIR}/squadvault_ci_workdb.XXXXXX")"
  if [[ -z "${WORK_DB}" ]]; then
    echo "ERROR: mktemp failed to create WORK_DB" >&2
    exit 2
  fi

  cleanup_work_db() { rm -f "${WORK_DB}" >/dev/null 2>&1 || true; }
  cp -p "${FIXTURE_DB}" "${WORK_DB}"

# CI: ensure downstream scripts read the finalized working DB (after mktemp + copy)
export CI_WORK_DB="${WORK_DB}"
export WORK_DB="${WORK_DB}"
  echo "    fixture_db=${FIXTURE_DB}"
  echo "    working_db=${WORK_DB}"
fi
# --- /Fixture DB working copy ---
export SQUADVAULT_TEST_DB="${WORK_DB}"

# Gate: enforce canonical test DB routing (v1)
./scripts/gate_no_xtrace_v1.sh

echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
gate_path="${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"
bash "$gate_path"

# SV_GATE: proof_registry_excludes_gates (v1) begin
bash scripts/gate_ci_guardrails_execution_order_lock_v1.sh
bash scripts/gate_ci_guardrails_ops_cluster_canonical_v1.sh
bash scripts/gate_ci_guardrails_ops_entrypoint_exactness_v1.sh
bash scripts/gate_ci_guardrails_ops_entrypoint_order_lock_v1.sh
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh
bash scripts/gate_ci_guardrails_ops_entrypoint_registry_completeness_v1.sh
bash scripts/gate_ci_guardrails_ops_label_registry_parity_v1.sh
bash scripts/gate_ci_guardrails_ops_label_source_exactness_v1.sh
bash scripts/gate_ci_guardrails_ops_renderer_shape_v1.sh
bash scripts/gate_ci_guardrails_ops_topology_uniqueness_v1.sh
bash scripts/gate_ci_guardrails_registry_authority_v1.sh
bash scripts/gate_ci_guardrails_registry_completeness_v1.sh
bash scripts/gate_ci_guardrails_surface_freeze_v1.sh


echo "==> Gate: no pasted terminal banners in scripts/"
echo "=== Gate: CI Milestones Latest bounded block (v1) ==="
bash scripts/gate_ci_milestones_latest_block_v1.sh
echo "==> Proof: terminal banner paste gate behavior (v1)"
# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP0="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end
echo "==> Proof: repo-root allowlist gate behavior (v1)"
# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_repo_root_allowlist_gate_behavior_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end
# SV_GATE: allowlist_patchers_insert_sorted (v1) begin
echo "=== Gate: CI proof runners block sorted (v1) ==="
bash scripts/gate_ci_proof_runners_block_sorted_v1.sh
bash scripts/gate_ci_proof_surface_registry_exactness_v1.sh
bash scripts/gate_ci_proof_surface_registry_index_discoverability_v1.sh
echo "=== Gate: prove_ci uses relative scripts invocations (v1) ==="
bash scripts/gate_ci_prove_ci_relative_script_invocations_v1.sh
# SV_GATE: allowlist_patchers_insert_sorted (v1) end

bash scripts/gate_ci_registry_execution_alignment_v1.sh


echo "==> Ops: patcher/wrapper pairing gate"
bash scripts/check_patch_pairs_v1.sh

# SV_PATCH_PROVE_CI_RETIRE_SEMANTICS_GATE_V2

# === Gate: retire semantics (v2) ===
# If the last commit message claims "retire", require that any removed patch scripts
# were archived under scripts/_retired/ in the same commit.
if git log -1 --pretty=%B | grep -qiE '\bretire(d)?\b'; then
  deleted_patch_scripts="$(git show --name-status --pretty="" HEAD | awk '$1=="D" && $2 ~ /^scripts\/(patch_|_patch_)/ {print $2}')"
  added_retired="$(git show --name-status --pretty="" HEAD | awk '$1=="A" && $2 ~ /^scripts\/_retired\// {print $2}')"
  if [[ -n "${deleted_patch_scripts}" && -z "${added_retired}" ]]; then
    echo "ERROR: retire semantics gate failed — commit message says retire, but deleted patch scripts without archiving under scripts/_retired/"
    echo "Deleted:"
    echo "${deleted_patch_scripts}" | sed 's/^/  - /'
    echo ""
    echo "Fix options:"
    echo "  - amend message (remove 'retire'), OR"
    echo "  - archive scripts under scripts/_retired/ in the same commit"
    exit 2
  fi
fi
# === End Gate: retire semantics (v2) ===

# ==> Gate: CI proof surface registry (v1)

# prove_ci_wire_ci_proof_surface_registry_index_discoverability_gate_v3
echo "==> Gate: CI proof surface registry discoverability in Ops index (v1)"
bash scripts/gate_ci_runtime_envelope_v1.sh

bash scripts/check_ci_proof_surface_matches_registry_v1.sh
echo "==> Filesystem ordering determinism gate"
./scripts/check_filesystem_ordering_determinism.sh

echo "==> Time & timestamp determinism gate"
./scripts/check_time_timestamp_determinism.sh
bash scripts/gate_contract_surface_manifest_hash_v1.sh

bash scripts/check_shell_syntax.sh
bash scripts/check_shims_compliance.sh
bash scripts/check_no_memory_reads.sh

bash scripts/gate_contracts_index_discoverability_v1.sh
bash scripts/check_no_pytest_directory_invocation.sh
# === SV_ANCHOR: docs_gates (v1) ===

# SV_GATE: docs_integrity (v2) begin
bash scripts/gate_creative_surface_fingerprint_canonical_v1.sh

bash scripts/gate_creative_surface_fingerprint_v1.sh
# SV_GATE: docs_integrity (v2) end

# SV_GATE: proof_registry_exactness (v1) begin
echo "=== Gate: Creative Surface Registry discoverability (v1) ==="
bash scripts/gate_creative_surface_registry_discoverability_v1.sh
# SV_GATE: proof_registry_exactness (v1) end


# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_docs_integrity_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end

# SV_GATE: docs_mutation_guardrail (v2) begin
echo "==> Docs mutation guardrail gate"
bash scripts/gate_creative_surface_registry_parity_v1.sh
# SV_GATE: docs_mutation_guardrail (v2) end

# Patch insertion point for doc/index gates.
# Patcher rule: insert additional doc/index gates immediately BELOW this block.
# === /SV_ANCHOR: docs_gates (v1) ===
# SV_GATE: proof_suite_completeness (v1) begin
echo "==> Proof suite completeness gate (v1)"
echo "=== Gate: Creative Surface registry usage (v1) ==="
bash scripts/gate_creative_surface_registry_usage_v1.sh
# SV_GATE: proof_suite_completeness (v1) end
# SV_GATE: ci_registry_execution_alignment (v1) begin
echo "==> Gate: CI registry → execution alignment (v1)"
bash scripts/gate_docs_integrity_v2.sh
# SV_GATE: ci_registry_execution_alignment (v1) end

echo "==> Gate: no double scripts prefix (v2)"

bash scripts/gate_docs_mutation_guardrail_v2.sh
bash scripts/gate_enforce_test_db_routing_v1.sh
bash scripts/gate_meta_surface_parity_v1.sh

echo "==> Gate: CI Guardrails ops entrypoints section + TOC (v2)"
# SV_GATE: ci_guardrails_ops_entrypoint_parity (v1) begin

## Indexed guardrails: execute to maintain ops index ↔ prove_ci parity
bash scripts/gate_no_bare_chevron_markers_v1.sh
bash scripts/gate_no_double_scripts_prefix_v2.sh
echo "=== Gate: Bash 3.2 builtin compatibility (v1) ==="
bash scripts/gate_no_mapfile_readarray_in_scripts_v1.sh
bash scripts/gate_no_network_in_ci_proofs_v1.sh
bash scripts/gate_no_terminal_banner_paste_v1.sh
bash scripts/gate_no_test_dir_case_drift_v1.sh
bash scripts/gate_no_untracked_patch_artifacts_v1.sh
bash scripts/gate_ops_indices_no_autofill_placeholders_v1.sh
bash scripts/gate_proof_suite_completeness_v1.sh
bash scripts/gate_proof_surface_registry_excludes_gates_v1.sh

## Best-in-class tightening: explicit execution surfaces (v1)
## (B) Contract boundary formalization
echo "=== Gate: prove_ci structure canonical (v1) ==="
bash scripts/gate_prove_ci_structure_canonical_v1.sh

## (C) Creative surface certification
echo "=== Gate: Pytest must only target tracked Tests/ (v1) ==="
bash scripts/gate_pytest_tracked_tests_only_v1.sh

# Creative surface fingerprint canonical drift gate (v1)
bash scripts/gate_repo_clean_after_proofs_v1.sh
bash scripts/gate_repo_root_allowlist_v1.sh
bash scripts/gate_rivalry_chronicle_contract_linkage_v1.sh
bash scripts/gate_standard_show_input_need_coverage_v1.sh

## (D) Meta surface parity
bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP0}" "prove_ci entry"

bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP_PROOF}" "after scripts/prove_docs_integrity_v1.sh"
# SV_GATE: ci_guardrails_ops_entrypoint_parity (v1) end
bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP_PROOF}" "after scripts/prove_eal_calibration_type_a_v1.sh"



# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_eal_calibration_type_a_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end
# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_tone_engine_type_a_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end
# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_version_presentation_navigation_type_a_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end

# SV_GATE: worktree_cleanliness_wrap_proof (v1) begin
SV_WORKTREE_SNAP_PROOF="$(scripts/gate_worktree_cleanliness_v1.sh begin)"
bash scripts/prove_signal_scout_tier1_type_a_v1.sh
# SV_GATE: worktree_cleanliness_wrap_proof (v1) end

# Golden path uses local db by default; point it at the fixture explicitly if supported.
# If prove_golden_path.sh already has flags, pass them here; otherwise we patch it next.
# Golden path uses local db by default; point it at the fixture explicitly if supported.
# If prove_golden_path.sh already has flags, pass them here; otherwise we patch it next.
if bash scripts/prove_golden_path.sh --help 2>/dev/null | grep -q -- '--db'; then
  SV_STRICT_EXPORTS=1 bash scripts/prove_golden_path.sh --db "${WORK_DB}" --league-id 70985 --season 2024 --week-index 6
else
  SV_STRICT_EXPORTS=1 bash scripts/prove_golden_path.sh
fi

echo
echo "=== CI: Rivalry Chronicle end-to-end (fixture) ==="
SV_PROVE_TS_UTC="2026-01-01T00:00:00Z" bash scripts/prove_rivalry_chronicle_end_to_end_v1.sh \
--db "${WORK_DB}" \
  --league-id 70985 \
  --season 2024 \
  --week-index 6 \
  --approved-by "ci"



# --- Fixture immutability guard (CI) ---
./scripts/check_fixture_immutability_ci.sh verify "${STATEFILE}" "${fixture_files[@]}"
# --- /Fixture immutability guard (CI) ---

# --- CI debug: DB source summary ---
if [[ "${WORK_DB}" == "${FIXTURE_DB}" ]]; then
  echo "CI DB source: fixture (read-only path used)"
else
  echo "CI DB source: temp working copy (derived from fixture)"
  echo "  fixture_db=${FIXTURE_DB}"
  echo "  working_db=${WORK_DB}"
fi
# --- /CI debug ---

echo "OK: CI proof suite passed"

echo "== Creative sharepack determinism (conditional) =="
bash scripts/prove_ci_creative_sharepack_if_available_v1.sh

echo "OK: CI working tree remained clean (guardrail enforced)."

# SV_GATE: ops_indices_no_autofill_placeholders (v1) begin
echo "==> Gate: Ops indices must not contain autofill placeholders (v1)"
bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP_PROOF}" "after scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh"
# SV_GATE: ops_indices_no_autofill_placeholders (v1) end



# SV_GATE: prove_creative_determinism (v1) begin
echo "==> Prove: creative determinism (v1)"
bash scripts/prove_creative_determinism_v1.sh
# SV_GATE: prove_creative_determinism (v1) end

# SV_GATE: rivalry_chronicle_contract_linkage (v1) begin
echo "==> Gate: Rivalry Chronicle contract linkage (v1)"
bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP_PROOF}" "after scripts/prove_signal_scout_tier1_type_a_v1.sh"
# SV_GATE: rivalry_chronicle_contract_linkage (v1) end

# SV_GATE: contracts_index_discoverability (v1) begin
echo "==> Gate: contracts index discoverability (v1)"
bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP_PROOF}" "after scripts/prove_tone_engine_type_a_v1.sh"

# SV_GATE: contract_surface_completeness (v1) begin
bash scripts/prove_contract_surface_completeness_v1.sh
# SV_GATE: contract_surface_completeness (v1) end

# SV_GATE: contracts_index_discoverability (v1) end

# SV_CI runtime envelope enforcement (best-effort; v1)
sv_rt_end="$(./scripts/py -c 'import time; print(int(time.time()))')"
export SV_CI_RUNTIME_SECONDS="$(( sv_rt_end - sv_rt_start ))"
bash scripts/gate_worktree_cleanliness_v1.sh assert "${SV_WORKTREE_SNAP_PROOF}" "after scripts/prove_version_presentation_navigation_type_a_v1.sh"

# # # <!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_BEGIN -->
echo "=== Gate: Enforce repo clean after proofs (v1) ==="

bash scripts/gate_worktree_cleanliness_v1.sh end "${SV_WORKTREE_SNAP0}"
# <!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_END -->
