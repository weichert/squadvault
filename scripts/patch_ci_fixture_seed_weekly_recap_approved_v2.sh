#!/usr/bin/env bash
set -euo pipefail

# Avoid exit-noise in environments that reference HISTTIMEFORMAT under -u.
: "${HISTTIMEFORMAT:=}"

echo "=== Patch wrapper: seed APPROVED weekly recap in CI fixture (v2) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

$py scripts/_patch_ci_fixture_seed_weekly_recap_approved_v2.py

$py - <<'PY'
import sqlite3
from pathlib import Path
db=Path("fixtures/ci_squadvault.sqlite")
conn=sqlite3.connect(str(db))
try:
    row=conn.execute("""
      SELECT id, version, state,
             LENGTH(COALESCE(rendered_text,'')) AS text_len,
             selection_fingerprint
      FROM recap_artifacts
      WHERE league_id=? AND season=? AND week_index=? AND artifact_type=? AND state='APPROVED'
      ORDER BY version DESC, id DESC
      LIMIT 1
    """, ("70985", 2024, 6, "WEEKLY_RECAP")).fetchone()
    if not row:
        raise SystemExit("ERROR: validation failed: no APPROVED WEEKLY_RECAP for week_06")
    if int(row[3]) <= 0:
        raise SystemExit("ERROR: validation failed: rendered_text empty")
    if not row[4]:
        raise SystemExit("ERROR: validation failed: selection_fingerprint empty")
    print(f"OK: APPROVED WEEKLY_RECAP present (id={row[0]} version={row[1]} text_len={row[3]} fp={row[4]})")
finally:
    conn.close()
PY

echo "OK"
