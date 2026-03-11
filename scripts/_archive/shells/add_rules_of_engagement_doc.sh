#!/usr/bin/env bash
set -euo pipefail

# SquadVault: add / refresh the Rules of Engagement doc (script-first standard).
# Usage:
#   ./scripts/add_rules_of_engagement_doc.sh

# Robust repo-root detection:
# - If running as a script file, BASH_SOURCE[0] exists.
# - If executed in a weird context, fall back to git.
if [[ -n "${BASH_SOURCE[0]:-}" ]]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
else
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
fi

cd "$ROOT"

PY_BIN="${PY_BIN:-python3}"

echo "=== SquadVault: Add/Refresh Rules of Engagement Doc ==="
echo "repo_root: $ROOT"
echo "python:    $PY_BIN"
echo

"$PY_BIN" "scripts/_add_rules_of_engagement_doc.py"

echo
echo "Done. Review with:"
echo "  git status"
echo "  git diff"
