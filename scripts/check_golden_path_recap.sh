#!/usr/bin/env bash
set -euo pipefail

SRC_DB="${1:-.local_squadvault.sqlite}"
LEAGUE_ID="${2:-70985}"
SEASON="${3:-2024}"
WEEK_INDEX="${4:-6}"
APPROVED_BY="${5:-steve}"

if [[ ! -f "$SRC_DB" ]]; then
  echo "ERROR: DB not found: $SRC_DB" >&2
  exit 2
fi

TMP_DB="$(mktemp -t squadvault_golden_path_XXXX.sqlite)"
cp "$SRC_DB" "$TMP_DB"

cleanup() {
  rm -f "$TMP_DB"
}
trap cleanup EXIT

say "=== SquadVault Golden Path Recap Checks (non-destructive) ==="
say "SRC_DB=$SRC_DB"
say "TMP_DB=$TMP_DB"
say "league=$LEAGUE_ID  season=$SEASON  week=$WEEK_INDEX  approved_by=$APPROVED_BY"
say ""
say "== 1) Golden path: no-delta (should skip approval cleanly) =="
PYTHONPATH=src python -u scripts/golden_path_recap_lifecycle.py \
  --db "$TMP_DB" \
  --league-id "$LEAGUE_ID" \
  --season "$SEASON" \
  --week-index "$WEEK_INDEX" \
  --approved-by "$APPROVED_BY" \
  --no-force-fallback
say ""
say "== 2) Golden path: forced path (should mint DRAFT then approve) =="
PYTHONPATH=src python -u scripts/golden_path_recap_lifecycle.py \
  --db "$TMP_DB" \
  --league-id "$LEAGUE_ID" \
  --season "$SEASON" \
  --week-index "$WEEK_INDEX" \
  --approved-by "$APPROVED_BY" \
  --legacy-force \
  --no-force-fallback
say ""
say "== 3) Invariant checks =="
PYTHONPATH=src python -u scripts/check_recap_approval_invariants.py \
  --db "$TMP_DB" \
  --league-id "$LEAGUE_ID" \
  --season "$SEASON" \
  --week-index "$WEEK_INDEX"
say ""
say "✅ OK: golden path + invariants passed (TMP_DB cleaned up)"
