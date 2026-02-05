#!/usr/bin/env bash
# SquadVault — local scratch cleanup + CI prove helper (v1)
#
# Local-only helper. NOT invoked by CI.
#
# Purpose:
#   - Detect common untracked scratch artifacts from iterative work:
#       scripts/_patch_*.py
#       scripts/patch_*.sh
#   - Print exactly what would be removed (deterministic ordering)
#   - Require SV_LOCAL_CLEAN=1 to actually delete anything
#   - If junk is present and SV_LOCAL_CLEAN!=1, exit nonzero (dry-run fail)
#   - When clean (or after cleaning), run: bash scripts/prove_ci.sh
#
# Notes:
#   - CWD-independent: resolves repo root via git rev-parse --show-toplevel
#   - bash3-safe: no mapfile, no assoc arrays

set -euo pipefail

die() {
  echo "ERROR: $*" 1>&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

need_cmd git
need_cmd grep
need_cmd sort
need_cmd rm

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || die "not in a git repo"
cd "$ROOT"

# Deterministic list of untracked files, filtered to our narrow scratch class.
# We intentionally do NOT touch tracked files, even if they match the patterns.
junk_list="$(
  git ls-files --others --exclude-standard     | grep -E '^(scripts/_patch_.*\.py|scripts/patch_.*\.sh)$'     | sort
)" || true

if [ -n "${junk_list}" ]; then
  echo "== Local scratch artifacts detected (untracked) =="
  echo "${junk_list}"
  echo

  if [ "${SV_LOCAL_CLEAN:-0}" != "1" ]; then
    echo "Dry-run mode (no deletions)."
    echo "To delete ONLY the files listed above and then run prove_ci:"
    echo "  SV_LOCAL_CLEAN=1 bash scripts/prove_local_clean_then_ci_v1.sh"
    exit 2
  fi

  echo "SV_LOCAL_CLEAN=1 set — removing listed scratch artifacts..."
  echo "${junk_list}" | while IFS= read -r p; do
    [ -n "$p" ] || continue
    rm -f -- "$p"
  done
  echo "OK: scratch artifacts removed."
  echo
else
  echo "OK: no matching local scratch artifacts found."
  echo
fi

echo "== Run CI prove suite =="
bash "$ROOT/scripts/prove_ci.sh"
