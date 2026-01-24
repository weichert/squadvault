#!/usr/bin/env bash
set -euo pipefail

DB="${DB:-.local_squadvault.sqlite}"
LEAGUE_ID="${LEAGUE_ID:-70985}"
SEASON="${SEASON:-2024}"
WEEK_INDEX="${WEEK_INDEX:-6}"
APPROVED_BY="${APPROVED_BY:-steve}"

# Canonical "created_at" used for Writing Room side-artifact metadata.
CREATED_AT_UTC="${CREATED_AT_UTC:-2026-01-23T00:00:00Z}"

WR_OUT="artifacts/writing_room/${LEAGUE_ID}/${SEASON}/week_$(printf '%02d' "${WEEK_INDEX}")/selection_set_v1.json"

echo "=== SquadVault: Writing Room side-artifact gate (v1) ==="
echo "DB=${DB}"
echo "League=${LEAGUE_ID} Season=${SEASON} Week=${WEEK_INDEX}"
echo "ApprovedBy=${APPROVED_BY}"
echo "CreatedAtUTC=${CREATED_AT_UTC}"
echo "WritingRoomOut=${WR_OUT}"
echo

echo "=== 1) Unit tests (Writing Room + CLI flag) ==="
./scripts/py -m unittest -v \
  Tests/test_writing_room_intake_v1_intentional_silence.py \
  Tests/test_recap_cli_writing_room_flag.py
echo

echo "=== 2) Non-destructive golden path check (WITH Writing Room) ==="
./scripts/recap.sh check \
  --db "${DB}" \
  --league-id "${LEAGUE_ID}" \
  --season "${SEASON}" \
  --week-index "${WEEK_INDEX}" \
  --enable-writing-room \
  --created-at-utc "${CREATED_AT_UTC}"
echo

echo "=== 3) Golden path lifecycle (WITH Writing Room) ==="
./scripts/recap.sh golden-path \
  --db "${DB}" \
  --league-id "${LEAGUE_ID}" \
  --season "${SEASON}" \
  --week-index "${WEEK_INDEX}" \
  --approved-by "${APPROVED_BY}" \
  --enable-writing-room \
  --created-at-utc "${CREATED_AT_UTC}"
echo

echo "=== 4) Verify Writing Room artifact exists ==="
if [[ ! -f "${WR_OUT}" ]]; then
  echo "ERROR: expected Writing Room artifact not found: ${WR_OUT}" >&2
  exit 2
fi
echo "OK: ${WR_OUT}"
echo

echo "=== 5) Summarize selection_set_v1.json ==="
./scripts/py - <<PY
import json
from collections import Counter

p = "${WR_OUT}"
with open(p, "r", encoding="utf-8") as f:
    ss = json.load(f)

included = ss.get("included_signal_ids") or []
excluded = ss.get("excluded") or []
withheld = bool(ss.get("withheld", False))
withheld_reason = ss.get("withheld_reason")

print(f"withheld: {withheld}")
if withheld:
    print(f"withheld_reason: {withheld_reason}")

print(f"included: {len(included)}")
print(f"excluded: {len(excluded)}")

rc = Counter([e.get("reason_code") for e in excluded])
if rc:
    print("excluded_by_reason:")
    for k, v in sorted(rc.items()):
        print(f"  - {k}: {v}")
PY

echo
echo "=== DONE: all gates passed ==="
