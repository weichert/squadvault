#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_status.sh"


DB="${DB:-.local_squadvault.sqlite}"
LEAGUE_ID="${1:?league_id required}"
MODE="${MODE:-full}"
SEASON="${2:?season required}"
WEEK_INDEX="${3:?week_index required}"
APPROVED_BY="${APPROVED_BY:-steve}"

ROOT="${ROOT:-path1_logs}"
RUN_TS="$(date -u +"%Y%m%dT%H%M%SZ")"
RUN_DIR="${ROOT}/league_${LEAGUE_ID}/season_${SEASON}/week_${WEEK_INDEX}/${RUN_TS}"
mkdir -p "${RUN_DIR}"

RUN_LOG="${RUN_DIR}/run.log"
OBS_LOG="${ROOT}/path1_weekly_log.md"

echo "=== Path1 Run ===" | tee -a "${RUN_LOG}"
echo "ts_utc: ${RUN_TS}" | tee -a "${RUN_LOG}"
echo "league_id: ${LEAGUE_ID}" | tee -a "${RUN_LOG}"
echo "season: ${SEASON}" | tee -a "${RUN_LOG}"
echo "week_index: ${WEEK_INDEX}" | tee -a "${RUN_LOG}"
echo "db: ${DB}" | tee -a "${RUN_LOG}"
echo "" | tee -a "${RUN_LOG}"

# --- RUN YOUR EXISTING COMMAND(S) HERE ---
# Replace the command below with whatever you already use as your weekly run.
# Keep it paste-safe and deterministic.
set +e

# MODE=render-only: observe only (render), do not touch lifecycle.
if [ "${MODE}" = "render-only" ]; then
  set +e
  PYTHONPATH=src python -u src/squadvault/consumers/recap_week_render.py \
    --db "${DB}" \
    --league-id "${LEAGUE_ID}" \
    --season "${SEASON}" \
    --week-index "${WEEK_INDEX}" \
    --suppress-render-warning \
    2>&1 | tee -a "${RUN_LOG}"
  EXIT_CODE="${PIPESTATUS[0]}"
  set -e

  echo "" | tee -a "${RUN_LOG}"
  echo "render-only mode: skipping lifecycle regeneration" | tee -a "${RUN_LOG}"
  echo "exit_code: ${EXIT_CODE}" | tee -a "${RUN_LOG}"
  exit "${EXIT_CODE}"
fi

# --- FULL MODE: lifecycle regeneration ---
PYTHONPATH=src python -u scripts/golden_path_recap_lifecycle.py \
  --db "${DB}" \
  --league-id "${LEAGUE_ID}" \
  --season "${SEASON}" \
  --week-index "${WEEK_INDEX}" \
  --approved-by "${APPROVED_BY}" \
  --no-force-fallback \
  2>&1 | tee -a "${RUN_LOG}"
EXIT_CODE="${PIPESTATUS[0]}"

set -e

echo "" | tee -a "${RUN_LOG}"
echo "exit_code: ${EXIT_CODE}" | tee -a "${RUN_LOG}"

# Minimal guided prompt for your Path 1 three-bullet log.
# (You answer separately via the note tool below—keeps runs clean.)
cat >> "${RUN_LOG}" <<EOF

Next step (Path 1):
- Run produced a recap or withheld.
- Make ONE decision: APPROVE / REGENERATE (conservative) / WITHHOLD.
- Then add your 3-line observation with:
  python scripts/path1_note.py "${OBS_LOG}" "${LEAGUE_ID}" "${SEASON}" "${WEEK_INDEX}" --did "..." --felt "..." --wanted "..."
EOF

exit "${EXIT_CODE}"
