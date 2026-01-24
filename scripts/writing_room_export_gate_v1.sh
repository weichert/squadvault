#!/usr/bin/env bash
set -euo pipefail

DB="${DB:-.local_squadvault.sqlite}"
LEAGUE_ID="${LEAGUE_ID:-70985}"
SEASON="${SEASON:-2024}"
WEEK_INDEX="${WEEK_INDEX:-6}"
CREATED_AT_UTC="${CREATED_AT_UTC:-2026-01-23T07:45:00Z}"

OUT_DIR="${OUT_DIR:-/tmp/sv_writing_room_export_gate_v1}"

echo "=== SquadVault: Writing Room export gate (v1) ==="
echo "=== Shim compliance ==="
bash scripts/check_shims_compliance.sh
echo
echo "DB=${DB}"
echo "League=${LEAGUE_ID} Season=${SEASON} Week=${WEEK_INDEX}"
echo "CreatedAtUTC=${CREATED_AT_UTC}"
echo "OutDir=${OUT_DIR}"
echo

echo "=== 1) Build Writing Room SelectionSetV1 side-artifact ==="
DB="${DB}" LEAGUE_ID="${LEAGUE_ID}" SEASON="${SEASON}" WEEK_INDEX="${WEEK_INDEX}" CREATED_AT_UTC="${CREATED_AT_UTC}" \
  bash scripts/writing_room_select_v1.sh
echo

echo "=== 2) Export approved narrative assemblies ==="
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

./scripts/py -u src/squadvault/consumers/recap_export_narrative_assemblies_approved.py \
  --db "${DB}" \
  --league-id "${LEAGUE_ID}" \
  --season "${SEASON}" \
  --week-index "${WEEK_INDEX}" \
  --export-dir "${OUT_DIR}"
echo

echo "=== 3) Verify Writing Room markers present in exports ==="
grep -RInE "BEGIN_WRITING_ROOM_SELECTION_SET_V1|END_WRITING_ROOM_SELECTION_SET_V1|## Writing Room \\(SelectionSetV1\\)" "${OUT_DIR}" >/dev/null
echo "OK: markers found"
echo

echo "=== DONE: export gate passed ==="
