#!/usr/bin/env bash
set -euo pipefail

: "${HISTTIMEFORMAT:=}"
: "${size:=}"

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

LEAGUE_ID="${LEAGUE_ID:-70985}"
SEASON="${SEASON:-2024}"
WEEK_INDEX="${WEEK_INDEX:-6}"
DB="${DB:-.local_squadvault.sqlite}"

export PYTHONPATH=".:src"

echo "== Proof Mode =="
echo "db=$DB"
echo "league=$LEAGUE_ID season=$SEASON week=$WEEK_INDEX"
echo

echo "== Tests =="
pytest -q Tests
echo

echo "== Export assemblies =="
./scripts/recap.py export-assemblies \
  --db "$DB" \
  --league-id "$LEAGUE_ID" \
  --season "$SEASON" \
  --week-index "$WEEK_INDEX"
echo

WEEK_DIR="artifacts/exports/${LEAGUE_ID}/${SEASON}/week_$(printf '%02d' "$WEEK_INDEX")"

if [[ ! -d "$WEEK_DIR" ]]; then
  echo "ERROR: week dir not found: $WEEK_DIR" >&2
  exit 2
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
  echo "ERROR: no approved assembly_plain_v1 found in: $WEEK_DIR" >&2
  echo "Expected pattern: assembly_plain_v1__approved_v*.md" >&2
  exit 2
fi
echo "Selected assembly: $ASSEMBLY"

echo "== NAC harness =="
python3 Tests/_nac_check_assembly_plain_v1.py "$ASSEMBLY"
echo

echo "OK: Golden path proof mode passed."
