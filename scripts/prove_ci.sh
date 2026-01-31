#!/usr/bin/env bash

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
  WORK_DB="$(mktemp "${SV_TMPDIR}/squadvault_ci_workdb.XXXXXX")"
  if [[ -z "${WORK_DB}" ]]; then
    echo "ERROR: mktemp failed to create WORK_DB" >&2
    exit 2
  fi

  cleanup_work_db() { rm -f "${WORK_DB}" >/dev/null 2>&1 || true; }
    cp -p "${FIXTURE_DB}" "${WORK_DB}"
  echo "    fixture_db=${FIXTURE_DB}"
  echo "    working_db=${WORK_DB}"
fi
# --- /Fixture DB working copy ---

# --- /Fixture immutability guard (CI) ---
set -euo pipefail

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


echo "== CI Proof Suite =="

bash scripts/check_shell_syntax.sh
bash scripts/check_shims_compliance.sh
bash scripts/check_no_memory_reads.sh

bash scripts/prove_eal_calibration_type_a_v1.sh
bash scripts/prove_tone_engine_type_a_v1.sh
bash scripts/prove_version_presentation_navigation_type_a_v1.sh

# Golden path uses local db by default; point it at the fixture explicitly if supported.
# If prove_golden_path.sh already has flags, pass them here; otherwise we patch it next.
if bash scripts/prove_golden_path.sh --help 2>/dev/null | grep -q -- '--db'; then
  bash scripts/prove_golden_path.sh --db "${WORK_DB}" --league-id 70985 --season 2024 --week-index 6
else
  bash scripts/prove_golden_path.sh
fi

echo
echo "=== CI: Rivalry Chronicle end-to-end (fixture) ==="
SV_PROVE_TS_UTC="2026-01-01T00:00:00Z" ./scripts/prove_rivalry_chronicle_end_to_end_v1.sh \
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

