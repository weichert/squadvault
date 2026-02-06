#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: recap_artifacts create_draft threads artifact_type through helper calls (v7) ==="

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

./scripts/py scripts/_patch_recap_artifacts_create_draft_thread_artifact_type_v7.py

echo
echo "Sniff (relevant helper callsites):"
grep -n "_latest_approved_fingerprint_in_conn(con, league_id, season, week_index" src/squadvault/core/recaps/recap_artifacts.py | head -n 20
grep -n "_latest_approved_version_in_conn(con, league_id, season, week_index" src/squadvault/core/recaps/recap_artifacts.py | head -n 20
grep -n "_latest_artifact_version_any_state(con, league_id, season, week_index" src/squadvault/core/recaps/recap_artifacts.py | head -n 20
grep -n "_next_version(con, league_id, season, week_index" src/squadvault/core/recaps/recap_artifacts.py | head -n 20

echo
echo "Compile check:"
./scripts/py - <<'PY'
import py_compile
py_compile.compile("src/squadvault/core/recaps/recap_artifacts.py", doraise=True)
print("OK: compile")
PY
