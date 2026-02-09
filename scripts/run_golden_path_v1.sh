#!/usr/bin/env bash
set -euo pipefail

# SquadVault — Human Golden Path Entrypoint (v1)
# Purpose:
#   One-command, CWD-independent demo runner for the Golden Path proof.
#
# Usage:
#   bash scripts/run_golden_path_v1.sh
# Env:
#   LEAGUE_ID, SEASON, WEEK_INDEX, DB
#   SV_KEEP_EXPORT_TMP=1  (preserve export temp dir for inspection)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "==> SquadVault: Golden Path (v1)"
echo "    repo_root=${REPO_ROOT}"
echo "    league=${LEAGUE_ID:-70985} season=${SEASON:-2024} week=${WEEK_INDEX:-6}"
echo

# Delegate to canonical proof runner.
bash scripts/prove_golden_path.sh

echo
echo "==> Done."
echo "TIP: Set SV_KEEP_EXPORT_TMP=1 to preserve the temp export dir."
