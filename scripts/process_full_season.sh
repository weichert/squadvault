#!/bin/bash
# Process entire 2024 season: select → draft → approve (or withhold empty weeks)
# Run from repo root: bash process_full_season.sh
set -e

DB=".local_squadvault.sqlite"
LEAGUE="70985"
SEASON=2024
APPROVED_BY="steve"

echo "=== Processing Full 2024 Season ==="
echo "DB: $DB | League: $LEAGUE | Season: $SEASON"
echo ""

# Step 1: Select and create recap_runs for all 18 weeks
echo "--- Step 1: Selection ---"
PYTHONPATH=src python3 << PYEOF
from squadvault.core.recaps.selection.weekly_selection_v1 import select_weekly_recap_events_v1
from squadvault.core.recaps.recap_runs import upsert_recap_run, RecapRunRecord

db, lid, s = "$DB", "$LEAGUE", $SEASON

for week in range(1, 19):
    sel = select_weekly_recap_events_v1(db_path=db, league_id=lid, season=s, week_index=week)
    n = len(sel.canonical_ids)
    upsert_recap_run(db, RecapRunRecord(
        league_id=lid, season=s, week_index=week, state="ELIGIBLE",
        window_mode=sel.window.mode,
        window_start=sel.window.window_start,
        window_end=sel.window.window_end,
        selection_fingerprint=sel.fingerprint,
        canonical_ids=[str(c) for c in sel.canonical_ids],
        counts_by_type=sel.counts_by_type,
    ))
    print(f"  Week {week:2d}: {sel.window.mode:14s} events={n:3d}  {sel.counts_by_type}")
PYEOF

echo ""

# Step 2: Generate drafts for all weeks
echo "--- Step 2: Generate Drafts ---"
for WEEK in $(seq 1 18); do
  echo -n "  Week $WEEK: "
  ./scripts/recap.sh regen --db "$DB" --league-id "$LEAGUE" --season "$SEASON" --week-index "$WEEK" --reason "full_season_process" --force 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'v{d[\"version\"]} {d[\"synced_recap_run_state\"]}')"
done

echo ""

# Step 3: Review — check which weeks have events vs empty
echo "--- Step 3: Review (event counts) ---"
PYTHONPATH=src python3 << 'PYEOF'
import sqlite3, json
con = sqlite3.connect(".local_squadvault.sqlite")
for week in range(1, 19):
    row = con.execute(
        "SELECT canonical_ids_json FROM recap_runs WHERE league_id='70985' AND season=2024 AND week_index=?",
        (week,),
    ).fetchone()
    ids = json.loads(row[0]) if row and row[0] else []
    status = "APPROVE" if len(ids) > 0 else "WITHHOLD (empty)"
    print(f"  Week {week:2d}: {len(ids):3d} events -> {status}")
con.close()
PYEOF

echo ""

# Step 4: Approve weeks with activity, withhold empty weeks
echo "--- Step 4: Approve / Withhold ---"
for WEEK in $(seq 1 16); do
  echo -n "  Week $WEEK: "
  ./scripts/recap.sh approve --db "$DB" --league-id "$LEAGUE" --season "$SEASON" --week-index "$WEEK" --approved-by "$APPROVED_BY" 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'APPROVED v{d[\"approved_version\"]}')"
done

# Withhold weeks 17-18 (zero events — silence preferred)
for WEEK in 17 18; do
  echo -n "  Week $WEEK: "
  # Get latest version
  VERSION=$(PYTHONPATH=src python3 -c "
import sqlite3
con = sqlite3.connect('$DB')
row = con.execute(
    '''SELECT version FROM recap_artifacts 
       WHERE league_id='$LEAGUE' AND season=$SEASON AND week_index=$WEEK AND artifact_type='WEEKLY_RECAP'
       ORDER BY version DESC LIMIT 1''',
).fetchone()
con.close()
print(row[0] if row else '')
")
  if [ -n "$VERSION" ]; then
    ./scripts/recap.sh withhold --db "$DB" --league-id "$LEAGUE" --season "$SEASON" --week-index "$WEEK" --version "$VERSION" --reason "zero_events_silence_preferred" 2>&1 | head -1
    echo "  WITHHELD v$VERSION (silence preferred — zero events)"
  else
    echo "  SKIP (no artifact)"
  fi
done

echo ""
echo "=== Season 2024 Complete ==="
echo ""

# Summary
PYTHONPATH=src python3 << 'PYEOF'
import sqlite3
con = sqlite3.connect(".local_squadvault.sqlite")
approved = con.execute(
    "SELECT COUNT(*) FROM recap_artifacts WHERE league_id='70985' AND season=2024 AND artifact_type='WEEKLY_RECAP' AND state='APPROVED'"
).fetchone()[0]
withheld = con.execute(
    "SELECT COUNT(*) FROM recap_artifacts WHERE league_id='70985' AND season=2024 AND artifact_type='WEEKLY_RECAP' AND state='WITHHELD'"
).fetchone()[0]
drafts = con.execute(
    "SELECT COUNT(*) FROM recap_artifacts WHERE league_id='70985' AND season=2024 AND artifact_type='WEEKLY_RECAP' AND state='DRAFT'"
).fetchone()[0]
total = con.execute(
    "SELECT COUNT(DISTINCT week_index) FROM recap_artifacts WHERE league_id='70985' AND season=2024 AND artifact_type='WEEKLY_RECAP'"
).fetchone()[0]
con.close()
print(f"Weeks covered: {total}")
print(f"  APPROVED:  {approved}")
print(f"  WITHHELD:  {withheld}")
print(f"  DRAFT:     {drafts}")
PYEOF
