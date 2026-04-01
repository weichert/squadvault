#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────
# Phase D — Player Scores Historical Backfill + Validation
#
# Prerequisites:
#   - Phases A, B, C committed (d9ae077+)
#   - Production DB at .local_squadvault.sqlite with 2024+2025 data
#   - ANTHROPIC_API_KEY set for recap generation
#
# What this does:
#   1. Ingests PLAYER_SCORES for 2024 and 2025 seasons
#   2. Canonicalizes both seasons
#   3. Re-selects and regenerates sample weeks with player highlights
#   4. Prints the generated recap text for commissioner review
#
# Run from repo root:
#   bash scripts/phase_d_player_backfill.sh
# ─────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

DB="${SQUADVAULT_DB:-.local_squadvault.sqlite}"
LEAGUE="70985"
DELAY=3.0

# Sample weeks to regenerate for validation
# Pick weeks with meaningful matchup data from each season
SAMPLE_2024=(1 6 14)
SAMPLE_2025=(1 6)

echo "================================================================"
echo "  Phase D — Player Scores Backfill + Validation"
echo "================================================================"
echo "  DB     : $DB"
echo "  League : $LEAGUE"
echo "  Delay  : ${DELAY}s"
echo ""

if [[ ! -f "$DB" ]]; then
  echo "ERROR: database not found at $DB" >&2
  exit 1
fi

# ── Step 1: Ingest PLAYER_SCORES ─────────────────────────────────────
echo ""
echo "Step 1: Ingest PLAYER_SCORES (2024 + 2025)"
echo "────────────────────────────────────────────"
echo "This fetches per-player weekly scores from MFL."
echo "Rate-limited: ~17 API calls per season × ${DELAY}s delay."
echo ""

./scripts/py -u src/squadvault/mfl/_run_historical_ingest.py \
  --db "$DB" \
  --league-id "$LEAGUE" \
  --use-history-chain \
  --categories PLAYER_SCORES \
  --delay "$DELAY"

echo ""
echo "Step 1 complete. PLAYER_SCORES ingested and canonicalized."

# ── Step 2: Verify player score counts ───────────────────────────────
echo ""
echo "Step 2: Verify ingestion"
echo "────────────────────────────────────────────"

./scripts/py -c "
from squadvault.core.storage.session import DatabaseSession

db, lid = '$DB', '$LEAGUE'
with DatabaseSession(db) as con:
    rows = con.execute('''
        SELECT season, COUNT(*) as n
        FROM canonical_events
        WHERE league_id = ? AND event_type = 'WEEKLY_PLAYER_SCORE'
        GROUP BY season
        ORDER BY season
    ''', (lid,)).fetchall()

if not rows:
    print('  WARNING: No WEEKLY_PLAYER_SCORE events found.')
else:
    print('  WEEKLY_PLAYER_SCORE canonical events by season:')
    for season, n in rows:
        print(f'    {season}: {n:,} events')
    print(f'    Total: {sum(n for _, n in rows):,}')
"

# ── Step 3: Re-select + regenerate sample weeks ──────────────────────
echo ""
echo "Step 3: Re-select and regenerate sample weeks"
echo "────────────────────────────────────────────"
echo "This re-runs selection (to pick up any new events)"
echo "then regenerates recaps with player highlights."
echo ""

for SEASON in 2024 2025; do
  if [[ "$SEASON" == "2024" ]]; then
    WEEKS=("${SAMPLE_2024[@]}")
  else
    WEEKS=("${SAMPLE_2025[@]}")
  fi

  for WEEK in "${WEEKS[@]}"; do
    echo "--- Season $SEASON, Week $WEEK ---"

    # Re-select (picks up WEEKLY_PLAYER_SCORE events in the window)
    ./scripts/py -c "
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_runs import upsert_recap_run, RecapRunRecord

sel = select_weekly_recap_events_v1(db_path='$DB', league_id='$LEAGUE', season=$SEASON, week_index=$WEEK)
n = len(sel.canonical_ids)
upsert_recap_run('$DB', RecapRunRecord(
    league_id='$LEAGUE', season=$SEASON, week_index=$WEEK, state='ELIGIBLE',
    window_mode=sel.window.mode,
    window_start=sel.window.window_start,
    window_end=sel.window.window_end,
    selection_fingerprint=sel.fingerprint,
    canonical_ids=[str(c) for c in sel.canonical_ids],
    counts_by_type=sel.counts_by_type,
))
print(f'  Selected: {n} events  {sel.counts_by_type}')
" 2>&1

    # Regenerate draft with force (player highlights now available)
    echo -n "  Regen: "
    ./scripts/recap.sh regen \
      --db "$DB" --league-id "$LEAGUE" \
      --season "$SEASON" --week-index "$WEEK" \
      --reason "phase_d_player_backfill" --force 2>&1 \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'v{d[\"version\"]} {d[\"synced_recap_run_state\"]}')"

    echo ""
  done
done

# ── Step 4: Print sample recaps for review ───────────────────────────
echo ""
echo "Step 4: Sample recaps for commissioner review"
echo "════════════════════════════════════════════════"
echo ""
echo "Review criteria (Recap Review Heuristic):"
echo "  - Does it mention players who carried or let down a team?"
echo "  - Are player names resolved (not raw IDs)?"
echo "  - Are player scores accurate (match the PLAYER HIGHLIGHTS data)?"
echo "  - Does it connect individual performances to matchup outcomes?"
echo "  - No fabricated player stats?"
echo ""

for SEASON in 2024 2025; do
  if [[ "$SEASON" == "2024" ]]; then
    WEEKS=("${SAMPLE_2024[@]}")
  else
    WEEKS=("${SAMPLE_2025[@]}")
  fi

  for WEEK in "${WEEKS[@]}"; do
    echo "╔══════════════════════════════════════════════╗"
    echo "║  Season $SEASON — Week $WEEK"
    echo "╚══════════════════════════════════════════════╝"
    ./scripts/recap.sh read \
      --db "$DB" --league-id "$LEAGUE" \
      --season "$SEASON" --week-index "$WEEK" 2>&1 || echo "  (no recap available)"
    echo ""
    echo "────────────────────────────────────────────────"
    echo ""
  done
done

echo ""
echo "================================================================"
echo "  Phase D complete."
echo ""
echo "  Next steps:"
echo "    1. Review the recaps above against the heuristic"
echo "    2. If player names show as raw IDs, verify player_directory"
echo "    3. Approve good weeks:  ./scripts/recap.sh approve ..."
echo "    4. Regenerate any week: ./scripts/recap.sh regen --force ..."
echo "================================================================"
