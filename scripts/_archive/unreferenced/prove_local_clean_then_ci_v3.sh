#!/usr/bin/env bash
# SquadVault — local scratch cleanup + CI prove helper (v3)
#
# Local-only helper. NOT invoked by CI.
#
# Tightened cleanup scope (v3):
#   ONLY untracked files matching the explicit scratch marker patterns:
#     - scripts/_patch__*.py
#     - scripts/patch__*.sh
#
# Default is dry-run:
#   - Prints exactly what it would remove (deterministic ordering)
#   - Exits nonzero if junk is present
#
# Destructive mode:
#   - Requires SV_LOCAL_CLEAN=1
#   - Deletes ONLY the listed untracked scratch files
#   - Then runs: bash scripts/prove_ci.sh
#
# Notes:
#   - CWD-independent: resolves repo root via git rev-parse --show-toplevel
#   - bash3-safe: no mapfile, no assoc arrays
#   - Safety: ONLY untracked files are candidates (tracked files are never removed)

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

echo "== Local cleaner scope (v3) =="
echo "Candidates are ONLY *untracked* files matching:"
echo "  - scripts/_patch__*.py"
echo "  - scripts/patch__*.sh"
echo "Tracked files are never removed."
echo

# Deterministic list of *untracked* files, filtered to the narrow scratch class.
junk_list="$(
  git ls-files --others --exclude-standard     | grep -E '^(scripts/_patch__.*\.py|scripts/patch__.*\.sh)$'     | sort
)" || true

if [ -n "${junk_list}" ]; then
  echo "== Local scratch artifacts detected (untracked) =="
  echo "${junk_list}"
  echo

  if [ "${SV_LOCAL_CLEAN:-0}" != "1" ]; then
    echo "Dry-run mode (no deletions)."
    echo "To delete ONLY the files listed above and then run prove_ci:"
    echo "  SV_LOCAL_CLEAN=1 bash scripts/prove_local_clean_then_ci_v3.sh"
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
