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
bash scripts/gate_enforce_test_db_routing_v1.sh

echo "=== Gate: CWD independence (shims) v1 ==="
repo_root_for_gate="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.." >/dev/null 2>&1
  pwd
)"
gate_path="${repo_root_for_gate}/scripts/gate_cwd_independence_shims_v1.sh"
echo "    repo_root_for_gate=${repo_root_for_gate}"
echo "    gate_path=${gate_path}"
if [[ ! -f "${gate_path}" ]]; then
  echo "ERROR: missing CWD gate: ${gate_path}"
  exit 1
fi
bash "${gate_path}"


# --- /Fixture immutability guard (CI) ---
set -euo pipefail

# === DETERMINISTIC EXECUTION ENVELOPE GATE (v1) ===
sv_fail_env() {
  echo "ERROR: deterministic env gate failed: $*" >&2
  exit 2
}
sv_require_kv() {
  local k="$1"
  local expected="$2"
  # Indirect expansion; treat unset as sentinel for clearer errors.
  local actual="${!k-unset}"
  if [[ "${actual}" != "${expected}" ]]; then
    sv_fail_env "${k} must be '${expected}' (got '${actual}')"
  fi
}
sv_require_kv "LC_ALL" "C"
sv_require_kv "LANG" "C"
sv_require_kv "TZ" "UTC"
sv_require_kv "PYTHONHASHSEED" "0"
echo "OK: deterministic env envelope"
# === /DETERMINISTIC EXECUTION ENVELOPE GATE (v1) ===

# === CI CLEANLINESS GUARDRAIL (v1) ===
# Enforce: CI proofs must not dirty the working tree.
# - Fail early if starting dirty
# - Fail on exit if anything dirtied the repo (even on proof failure)
./scripts/check_repo_cleanliness_ci.sh --phase before
sv_ci_on_exit() {
  # Safe temp cleanup (outside repo)
  rm -f "${WORK_DB:-}" "${STATEFILE:-}" >/dev/null 2>&1 || true
  # Repo cleanliness guardrail (no cleanup / no masking)
  ./scripts/check_repo_cleanliness_ci.sh --phase after
}
trap 'sv_ci_on_exit' EXIT
# === /CI CLEANLINESS GUARDRAIL (v1) ===

echo "== CI Proof Suite ==
echo "==> Ops: patcher/wrapper pairing gate"
bash scripts/check_patch_pairs_v1.sh
"

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
bash scripts/check_ci_proof_surface_matches_registry_v1.sh
echo "==> Filesystem ordering determinism gate"
./scripts/check_filesystem_ordering_determinism.sh

echo "==> Time & timestamp determinism gate"
./scripts/check_time_timestamp_determinism.sh

bash scripts/check_shell_syntax.sh
bash scripts/check_shims_compliance.sh
bash scripts/check_no_memory_reads.sh

bash scripts/check_no_pytest_directory_invocation.sh
bash scripts/prove_docs_integrity_v1.sh

bash scripts/prove_eal_calibration_type_a_v1.sh
bash scripts/prove_tone_engine_type_a_v1.sh
bash scripts/prove_version_presentation_navigation_type_a_v1.sh

bash scripts/prove_signal_scout_tier1_type_a_v1.sh

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
echo "OK: CI working tree remained clean (guardrail enforced)."
