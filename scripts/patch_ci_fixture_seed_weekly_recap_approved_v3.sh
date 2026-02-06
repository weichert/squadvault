#!/usr/bin/env bash
set -euo pipefail
: "${HISTTIMEFORMAT:=}"

echo "=== Patch wrapper: seed APPROVED weekly recap in CI fixture (v3) ==="

if [ -x "scripts/py" ]; then
  py="scripts/py"
else
  py="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ci_fixture_seed_weekly_recap_approved_v3.py

echo "==> validate: header present in fixture row"
$py - <<'PY'
import sqlite3
from pathlib import Path
db = Path("fixtures/ci_squadvault.sqlite")
conn = sqlite3.connect(str(db))
try:
    row = conn.execute(
        """
        SELECT rendered_text
        FROM recap_artifacts
        WHERE league_id='70985'
          AND season=2024
          AND week_index=6
          AND artifact_type='WEEKLY_RECAP'
          AND state='APPROVED'
        ORDER BY version DESC, id DESC
        LIMIT 1
        """
    ).fetchone()
    assert row, "missing APPROVED WEEKLY_RECAP row"
    txt = row[0] or ""
    assert "## What happened (facts)" in txt, "missing required header"
    print("OK: fixture recap includes required header")
finally:
    conn.close()
PY

echo "OK"
