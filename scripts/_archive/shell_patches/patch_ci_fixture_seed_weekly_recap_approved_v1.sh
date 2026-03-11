#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: seed APPROVED WEEKLY_RECAP in CI fixture (v1) ==="

# CWD-independent + bash3-safe
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"
cd "$repo_root"

py="$repo_root/scripts/py"
if [ -x "$py" ]; then
  python_exec="$py"
else
  python_exec="${PYTHON:-python}"
fi

./scripts/py scripts/_patch_ci_fixture_seed_weekly_recap_approved_v1.py

echo "==> validate: APPROVED WEEKLY_RECAP exists for 70985/2024/week_06"
"$python_exec" - <<'PY'
import sqlite3
db="fixtures/ci_squadvault.sqlite"
con=sqlite3.connect(db)
row=con.execute("""
  SELECT id, version, state, LENGTH(rendered_text), selection_fingerprint
  FROM recap_artifacts
  WHERE league_id=? AND season=? AND week_index=? AND artifact_type=?
    AND state='APPROVED'
  ORDER BY version DESC
  LIMIT 1
""", ("70985", 2024, 6, "WEEKLY_RECAP")).fetchone()
if not row:
    raise SystemExit("ERROR: validation failed: no APPROVED WEEKLY_RECAP for week_06")
print(f"OK: APPROVED WEEKLY_RECAP present (id={row[0]} version={row[1]} text_len={row[3]} fp={row[4]})")
PY

echo "==> git status (expect fixture modified if it needed seeding/promotion)"
git status --porcelain=v1

echo "OK"
