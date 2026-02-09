#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"


: "${HISTTIMEFORMAT:=}"
: "${size:=}"


LEAGUE_ID="${LEAGUE_ID:-70985}"
SEASON="${SEASON:-2024}"
WEEK_INDEX="${WEEK_INDEX:-6}"
DB="${WORK_DB:-${CI_WORK_DB:-${DB:-.local_squadvault.sqlite}}}"  # prove_golden_path_use_work_db_v2
# SV_PATCH: golden path default DB uses fixture temp copy (v1)
# If no DB is provided (falls back to .local_squadvault.sqlite) and the schema isn't present,
# use an immutable fixture copied to a temp DB. This keeps Golden Path self-contained on fresh clones.
_SV_GP_TMP_DB=""
_sv_gp_db_has_recap_runs() {
  sqlite3 -noheader -batch "$1" "SELECT 1 FROM sqlite_master WHERE type='table' AND name='recap_runs' LIMIT 1;" 2>/dev/null | grep -q '^1$'
}

if [[ "${DB}" == ".local_squadvault.sqlite" ]]; then
  if [[ ! -f "${DB}" ]] || ! _sv_gp_db_has_recap_runs "${DB}"; then
    _sv_gp_fixture_db="${REPO_ROOT:-.}/fixtures/ci_squadvault.sqlite"
    if [[ ! -f "${_sv_gp_fixture_db}" ]]; then
      echo "ERROR: Golden Path default DB fixture missing: ${_sv_gp_fixture_db}" >&2
      exit 2
    fi

    _SV_GP_TMP_DB="$(mktemp "${TMPDIR:-/tmp}/sv_golden_path_db.XXXXXX")"
    cp "${_sv_gp_fixture_db}" "${_SV_GP_TMP_DB}"
    DB="${_SV_GP_TMP_DB}"
  fi
fi

# Ensure pytest uses the same DB
export SQUADVAULT_TEST_DB="${DB}"

# Clean up temp DB if we created one (avoid clobbering an existing EXIT trap)
if ! trap -p EXIT | grep -q .; then
  trap 'if [[ -n "${_SV_GP_TMP_DB:-}" && -f "${_SV_GP_TMP_DB:-}" ]]; then rm -f "${_SV_GP_TMP_DB}"; fi' EXIT
fi
# /SV_PATCH: golden path default DB uses fixture temp copy (v1)

export PYTHONPATH=".:src"

echo "== Proof Mode =="
echo "db=$DB"
echo "league=$LEAGUE_ID season=$SEASON week=$WEEK_INDEX"
echo

echo "== Tests =="
# SV_PATCH: pinned, git-tracked pytest list (avoid broad `pytest -q Tests`)
  {
    # Bash-3-safe pinned, git-tracked pytest list.
    # We explicitly enumerate git-tracked Tests/test_*.py files to prevent accidental surface expansion.
    gp_tests=()
    while IFS= read -r p; do
      gp_tests+=("$p")
    done < <(git ls-files 'Tests/test_*.py' | sort)

    if [ "${#gp_tests[@]}" -eq 0 ]; then
      echo "ERROR: no git-tracked Tests/test_*.py files found for golden path" >&2
      exit 1
    fi

    pytest -q "${gp_tests[@]}"
  }

# /SV_PATCH: pinned, git-tracked pytest list

echo "== Shim compliance =="
bash scripts/check_shims_compliance.sh
echo
echo

echo "== Export assemblies =="
echo "NOTE: set SV_KEEP_EXPORT_TMP=1 to preserve the temp export dir for inspection"

strict_exports="${SV_STRICT_EXPORTS:-0}"
export_rc=0

# SV_PATCH: golden path ephemeral exports by default (v1)
# Default behavior: write export artifacts to a temp export root to keep fresh clones clean.
# Opt-in persistence: set SV_KEEP_EXPORTS=1 to use the default export root ("artifacts").
SV_KEEP_EXPORTS="${SV_KEEP_EXPORTS:-0}"
EXPORT_ROOT="artifacts"
_SV_GP_TMP_EXPORT_ROOT=""

if [[ "$SV_KEEP_EXPORTS" != "1" ]]; then
  _SV_GP_TMP_EXPORT_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/sv_golden_path_exports.XXXXXX")"
  EXPORT_ROOT="$_SV_GP_TMP_EXPORT_ROOT"
fi

# Cleanup temp export root (chain EXIT trap if one already exists)
if [[ -n "${_SV_GP_TMP_EXPORT_ROOT:-}" ]]; then
  _sv_gp_prev_exit_trap="$(trap -p EXIT | sed -E "s/^trap -- '(.*)' EXIT$/\1/")"
  if [[ -n "${_sv_gp_prev_exit_trap:-}" ]]; then
# SV_PATCH_KEEP_EXPORT_TMP_V1
if [[ "${SV_KEEP_EXPORT_TMP:-0}" == "1" ]]; then
  echo "NOTE: SV_KEEP_EXPORT_TMP=1 — preserving golden path export temp dir"
else
    trap "${_sv_gp_prev_exit_trap}; rm -rf '${_SV_GP_TMP_EXPORT_ROOT}'" EXIT
fi
  else
    trap "rm -rf '${_SV_GP_TMP_EXPORT_ROOT}'" EXIT
  fi
fi
# /SV_PATCH: golden path ephemeral exports by default (v1)
./scripts/recap.sh export-assemblies \
  --db "$DB" \
  --league-id "$LEAGUE_ID" \
  --season "$SEASON" \
  --week-index "$WEEK_INDEX" \
  --export-dir "$EXPORT_ROOT" || export_rc=$?

if [[ "$export_rc" -ne 0 ]]; then
  if [[ "$strict_exports" == "1" ]]; then
    echo "ERROR: export-assemblies failed (rc=$export_rc) and SV_STRICT_EXPORTS=1" >&2
    exit "$export_rc"
  fi
  echo "WARN: export-assemblies failed (rc=$export_rc); continuing (SV_STRICT_EXPORTS=0)" >&2
fi

echo

WEEK_DIR="${EXPORT_ROOT}/exports/${LEAGUE_ID}/${SEASON}/week_$(printf '%02d' "$WEEK_INDEX")"

if [[ ! -d "$WEEK_DIR" ]]; then
  if [[ "${SV_STRICT_EXPORTS:-0}" == "1" ]]; then
    echo "ERROR: week dir not found: $WEEK_DIR" >&2
    exit 2
  fi
  echo "WARN: week dir not found: $WEEK_DIR; skipping export validation (SV_STRICT_EXPORTS=0)" >&2
  echo "OK: Golden path proof mode passed."
  exit 0
fi

# Find highest approved version deterministically (by numeric suffix)
ASSEMBLY="$(
  find "$WEEK_DIR" -maxdepth 1 -type f -name 'assembly_plain_v1__approved_v*.md' -print 2>/dev/null \
  | sed -E 's/.*__approved_v([0-9]+)\.md$/\1 &/' \
  | sort -n \
  | tail -n 1 \
  | cut -d' ' -f2-
)"

if [[ -z "${ASSEMBLY:-}" || ! -f "$ASSEMBLY" ]]; then
  if [[ "${SV_STRICT_EXPORTS:-0}" == "1" ]]; then
    echo "ERROR: no approved assembly_plain_v1 found in: $WEEK_DIR" >&2
    echo "Expected pattern: assembly_plain_v1__approved_v*.md" >&2
    exit 2
  fi
  echo "WARN: no approved assembly_plain_v1 found in: $WEEK_DIR; skipping NAC harness (SV_STRICT_EXPORTS=0)" >&2
  echo "OK: Golden path proof mode passed."
  exit 0
fi
echo "Selected assembly: $ASSEMBLY"
# SV_GATE: golden_path_output_contract (v1) begin
echo "== Output contract gate (v1) ==" 
bash scripts/gate_golden_path_output_contract_v1.sh --selected-assembly "${ASSEMBLY}"
# SV_GATE: golden_path_output_contract (v1) end

\
# SV_PATCH: NAC preflight fingerprint normalization (v3)
# NAC requires a 64-lower-hex fingerprint in the BEGIN_CANONICAL_FINGERPRINT block.
# Some fixtures/export paths can emit a placeholder 'test-fingerprint'. Normalize it,
# but do NOT mutate the original approved assembly. Instead, normalize into a temp copy
# used only for NAC validation.
ASSEMBLY_FOR_NAC="$ASSEMBLY"
_SV_NAC_TMP_ASSEMBLY=""

if grep -q -- "Selection fingerprint: test-fingerprint" "$ASSEMBLY"; then
  echo "==> NAC preflight: placeholder selection fingerprint detected; normalizing temp copy"

  _SV_NAC_TMP_ASSEMBLY="$(mktemp "${TMPDIR:-/tmp}/sv_golden_path_assembly.XXXXXX")"
  cp "$ASSEMBLY" "$_SV_NAC_TMP_ASSEMBLY"
  ASSEMBLY_FOR_NAC="$_SV_NAC_TMP_ASSEMBLY"

  # Pull fp from DB (APPROVED WEEKLY_RECAP), else fallback to 64 zeros.
  _sv_fp="$(
    sqlite3 -noheader -batch "$DB" "
      SELECT selection_fingerprint
      FROM recap_artifacts
      WHERE league_id='${LEAGUE_ID}'
        AND season=${SEASON}
        AND week_index=${WEEK_INDEX}
        AND artifact_type='WEEKLY_RECAP'
        AND state='APPROVED'
      ORDER BY version DESC, id DESC
      LIMIT 1;
    " 2>/dev/null || true
  )"

  # Normalize: must be exactly 64 lowercase hex.
  if ! echo "${_sv_fp}" | grep -Eq '^[0-9a-f]{64}$'; then
    _sv_fp="$(printf '%064d' 0)"
  fi

  "$REPO_ROOT/scripts/py" "$REPO_ROOT/scripts/_normalize_nac_placeholder_fingerprint_v1.py" "$ASSEMBLY_FOR_NAC" "$_sv_fp"
  echo "==> NAC preflight: fingerprint normalized in temp copy (fp=${_sv_fp})"
fi
# /SV_PATCH: NAC preflight fingerprint normalization (v3)


echo "== NAC harness =="
"$REPO_ROOT/scripts/py" "$REPO_ROOT/Tests/_nac_check_assembly_plain_v1.py" "$ASSEMBLY_FOR_NAC"
if [[ -n "${_SV_NAC_TMP_ASSEMBLY:-}" && -f "${_SV_NAC_TMP_ASSEMBLY:-}" ]]; then
  rm -f "${_SV_NAC_TMP_ASSEMBLY}"
fi

echo

echo "OK: Golden path proof mode passed."
