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

ASSEMBLY="artifacts/exports/${LEAGUE_ID}/${SEASON}/week_$(printf '%02d' "$WEEK_INDEX")/assembly_plain_v1__approved_v11.md"
if [[ ! -f "$ASSEMBLY" ]]; then
  echo "ERROR: expected assembly not found: $ASSEMBLY" >&2
  echo "Tip: set WEEK_INDEX/LEAGUE_ID/SEASON or update the expected filename if approval version changes." >&2
  exit 2
fi

echo "== NAC harness =="
python3 Tests/_nac_check_assembly_plain_v1.py "$ASSEMBLY"
echo

echo "OK: Golden path proof mode passed."
