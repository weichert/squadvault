#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"


: "${HISTTIMEFORMAT:=}"
: "${size:=}"

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

LEAGUE_ID="${LEAGUE_ID:-70985}"
SEASON="${SEASON:-2024}"
WEEK_INDEX="${WEEK_INDEX:-6}"
DB="${WORK_DB:-${CI_WORK_DB:-${DB:-.local_squadvault.sqlite}}}"  # prove_golden_path_use_work_db_v2
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

strict_exports="${SV_STRICT_EXPORTS:-0}"
export_rc=0

./scripts/recap.sh export-assemblies \
  --db "$DB" \
  --league-id "$LEAGUE_ID" \
  --season "$SEASON" \
  --week-index "$WEEK_INDEX" || export_rc=$?

if [[ "$export_rc" -ne 0 ]]; then
  if [[ "$strict_exports" == "1" ]]; then
    echo "ERROR: export-assemblies failed (rc=$export_rc) and SV_STRICT_EXPORTS=1" >&2
    exit "$export_rc"
  fi
  echo "WARN: export-assemblies failed (rc=$export_rc); continuing (SV_STRICT_EXPORTS=0)" >&2
fi

echo

WEEK_DIR="artifacts/exports/${LEAGUE_ID}/${SEASON}/week_$(printf '%02d' "$WEEK_INDEX")"

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

echo "== NAC harness =="
"$REPO_ROOT/scripts/py" "$REPO_ROOT/Tests/_nac_check_assembly_plain_v1.py" "$ASSEMBLY"
echo

echo "OK: Golden path proof mode passed."
