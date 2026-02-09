#!/usr/bin/env bash
# SquadVault — gate: no untracked patch artifacts (v1)
# Fails if there are untracked patcher/wrapper artifacts in scripts/:
#   ?? scripts/_patch_*.py
#   ?? scripts/patch_*.sh
#
# Rationale:
# Prevent WIP patch artifacts from unexpectedly breaking prove_ci
# "repo-cleanliness preconditions" / clean working tree assumptions.

set -euo pipefail

# CWD-independence: resolve repo root relative to this script location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export LC_ALL=C

porcelain="$(git status --porcelain=v1)"

# Only untracked lines matter ("?? ..."). Tracked modifications are handled elsewhere.
# Match:
#   ?? scripts/_patch_*.py
#   ?? scripts/patch_*.sh
hits="$(printf "%s\n" "${porcelain}" | grep -E '^\?\?[[:space:]]+scripts/(_patch_.*\.py|patch_.*\.sh)$' || true)"

# Note: `git status --porcelain=v1` untracked prefix is literally "??", but
# we keep the pattern robust to the leading 2-status columns.
if [[ -n "${hits}" ]]; then
  {
    echo "ERROR: Untracked patch artifacts detected in scripts/ (gate_no_untracked_patch_artifacts_v1)"
    echo
    echo "These files match untracked patcher/wrapper patterns and will break repo-cleanliness assumptions:"
    echo
    printf "%s\n" "${hits}"
    echo
    echo "HINT: Remediation options"
    echo "  1) Inspect:"
    echo "       git status --porcelain=v1"
    echo
    echo "  2) If WIP / accidental, remove them:"
    echo "       rm -f <file> [<file> ...]"
    echo
    echo "  3) If intentional, add + commit them:"
    echo "       git add <file> [<file> ...]"
    echo
    echo "  4) If you really want destructive cleanup of ALL untracked files/dirs:"
    echo "       git clean -fd"
    echo
  } >&2
  exit 1
fi

echo "OK: No untracked patch artifacts found in scripts/ (v1)"
exit 0
