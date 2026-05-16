#!/usr/bin/env bash
set -euo pipefail

# scripts/run_weekly_ingest.sh
# Track D scheduler wrapper — calls run_ingest_then_canonicalize.py
# for the configured season. Invoked by launchd Tuesday mornings.
#
# Configuration: update SEASON each year before the new NFL season.
# LEAGUE_ID is fixed (PFL Buddies canonical ID).
#
# Missed launchd windows are NOT retried at wakeup.
# If Tuesday's run is missed, run this script manually:
#   bash scripts/run_weekly_ingest.sh

# --- Configuration (update SEASON each year) ---
SEASON=2025
LEAGUE_ID=70985

# --- Paths ---
REPO_ROOT="$(cd "$(dirname "$0")/.." >/dev/null 2>&1 && pwd)"
DB_PATH="${REPO_ROOT}/.local_squadvault.sqlite"
LOG_DIR="${REPO_ROOT}/logs"
LOG_PATH="${LOG_DIR}/ingest_$(date +%Y%m%d_%H%M%S).log"

# --- Setup ---
cd "${REPO_ROOT}"
mkdir -p "${LOG_DIR}"

echo "[$(date -u +%FT%TZ)] Starting ingest season=${SEASON} league=${LEAGUE_ID}" | tee -a "${LOG_PATH}"

# Load .env.local — contains MFL_SERVER, MFL_USERNAME, MFL_PASSWORD.
# The Python script only auto-loads .env; we source .env.local explicitly here.
if [[ -f "${REPO_ROOT}/.env.local" ]]; then
    set -a
    source "${REPO_ROOT}/.env.local"
    set +a
else
    echo "[$(date -u +%FT%TZ)] ERROR: .env.local not found at ${REPO_ROOT}/.env.local" | tee -a "${LOG_PATH}"
    exit 1
fi

# --- Run ---
"${REPO_ROOT}/scripts/py"     "${REPO_ROOT}/src/squadvault/ops/run_ingest_then_canonicalize.py"     --db "${DB_PATH}"     --league-id "${LEAGUE_ID}"     --season "${SEASON}"     >> "${LOG_PATH}" 2>&1

EXIT_CODE=$?
echo "[$(date -u +%FT%TZ)] Ingest exited with code ${EXIT_CODE}" | tee -a "${LOG_PATH}"
exit ${EXIT_CODE}
