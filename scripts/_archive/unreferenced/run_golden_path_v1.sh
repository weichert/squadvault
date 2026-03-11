#!/usr/bin/env bash
# Contract doc (reference): docs/contracts/golden_path_output_contract_v1.md
# NOTE: This script is NOT a contract enforcement surface.
#       Enforcement happens in scripts/gate_golden_path_output_contract_v1.sh (and via scripts/prove_golden_path.sh).


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
