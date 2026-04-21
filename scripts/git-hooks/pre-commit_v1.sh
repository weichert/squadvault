#!/usr/bin/env bash
# SquadVault — git pre-commit hook (v1)
#
# Purpose:
#   Prevent common repo hygiene violations from ever entering commits.
#
# Escape hatch:
#   SV_SKIP_PRECOMMIT=1 -> skip checks, exit 0
#
# Notes:
#   - This file is repo-tracked. Install manually into .git/hooks/pre-commit:
#       cp scripts/git-hooks/pre-commit_v1.sh .git/hooks/pre-commit
#       chmod +x .git/hooks/pre-commit
#     Re-run after any changes to this file to keep the installed hook in
#     sync with the tracked version.
#   - Keep bash3-safe.

set -euo pipefail

if [[ "${SV_SKIP_PRECOMMIT:-0}" == "1" ]]; then
  echo "WARN: SV_SKIP_PRECOMMIT=1 set — skipping pre-commit checks."
  exit 0
fi

# Repo-root anchored (pre-commit may be invoked from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

echo "==> pre-commit: terminal banner paste gate"
bash scripts/gate_no_terminal_banner_paste_v1.sh

echo "==> pre-commit: no-xtrace guardrail gate"
bash scripts/gate_no_xtrace_v1.sh

echo "==> pre-commit: repo-root allowlist gate"
bash scripts/gate_repo_root_allowlist_v1.sh

echo "OK: pre-commit checks passed."
