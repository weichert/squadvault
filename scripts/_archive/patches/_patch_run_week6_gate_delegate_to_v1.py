from pathlib import Path

p = Path("scripts/run_week6_writing_room_gate.sh")
s = p.read_text(encoding="utf-8")

# Guard: ensure we're patching the expected script (must contain prior banner)
if "=== SquadVault: Writing Room side-artifact gate ===" not in s and "run_week6_writing_room_gate.sh" not in str(p):
    raise SystemExit("ERROR: unexpected file contents; refusing to patch.")

new = """#!/usr/bin/env bash
set -euo pipefail

# Delegator: preserved legacy entrypoint for Week 6 Writing Room gate.
# Source of truth: scripts/run_writing_room_gate_v1.sh
#
# You may override any variable via env (DB, LEAGUE_ID, SEASON, WEEK_INDEX, APPROVED_BY, CREATED_AT_UTC).

DB="${DB:-.local_squadvault.sqlite}"
LEAGUE_ID="${LEAGUE_ID:-70985}"
SEASON="${SEASON:-2024}"
WEEK_INDEX="${WEEK_INDEX:-6}"
APPROVED_BY="${APPROVED_BY:-steve}"
CREATED_AT_UTC="${CREATED_AT_UTC:-2026-01-22T00:00:00Z}"

export DB LEAGUE_ID SEASON WEEK_INDEX APPROVED_BY CREATED_AT_UTC
exec "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/run_writing_room_gate_v1.sh"
"""

p.write_text(new, encoding="utf-8")
print("OK: scripts/run_week6_writing_room_gate.sh now delegates to run_writing_room_gate_v1.sh")
