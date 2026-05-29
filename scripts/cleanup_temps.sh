#!/usr/bin/env bash
# scripts/cleanup_temps.sh — Manual cleanup of stale SquadVault temp dirs.
#
# Pytest tmp_path fixtures, prove_ci working DBs, golden-path exports,
# worktree-porcelain gates, and creative-drift proofs accumulate under
# $TMPDIR (typically /var/folders/.../T on macOS) across aborted runs.
# This script removes directories matching known SquadVault prefixes
# that have not been modified in the last N hours.
#
# This is a MANUAL tool. It is NOT invoked by prove_ci or any gate.
# Run it when prove_ci feels slow, after a series of aborted CI sweeps,
# or as routine hygiene.
#
# Usage:
#   scripts/cleanup_temps.sh                  # clean temps older than 24h
#   scripts/cleanup_temps.sh --age-hours 1    # clean temps older than 1h
#   scripts/cleanup_temps.sh --dry-run        # list candidates only
#
# Exit codes:
#   0 — success (including "nothing to clean")
#   1 — invalid argument
#   2 — TMPDIR resolution failed
set -euo pipefail

AGE_HOURS=24
DRY_RUN=0

print_help() {
  cat <<HELP
scripts/cleanup_temps.sh — Manual SquadVault temp-dir cleanup.

Usage:
  scripts/cleanup_temps.sh [--age-hours N] [--dry-run]
  scripts/cleanup_temps.sh --help

Options:
  --age-hours N   Only remove temps older than N hours (default: 24).
  --dry-run       List candidates without removing anything.
  --help, -h      Show this message.
HELP
}

while [ $# -gt 0 ]; do
  case "$1" in
    --age-hours)
      AGE_HOURS="${2:-}"
      if ! [[ "$AGE_HOURS" =~ ^[0-9]+$ ]]; then
        echo "ERROR: --age-hours requires a non-negative integer, got: ${AGE_HOURS}" >&2
        exit 1
      fi
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      echo "Run with --help for usage." >&2
      exit 1
      ;;
  esac
done

AGE_MINUTES=$(( AGE_HOURS * 60 ))

# Resolve TMPDIR base. mktemp -u emits a candidate path without
# creating anything; dirname extracts the directory.
TMP_CANDIDATE="$(mktemp -u 2>/dev/null || true)"
if [ -z "${TMP_CANDIDATE}" ]; then
  echo "ERROR: could not resolve TMPDIR (mktemp -u failed)" >&2
  exit 2
fi
TMPDIR_BASE="$(dirname "${TMP_CANDIDATE}")"

if [ ! -d "${TMPDIR_BASE}" ]; then
  echo "ERROR: resolved TMPDIR_BASE does not exist: ${TMPDIR_BASE}" >&2
  exit 2
fi

# Known SquadVault temp-dir prefixes (from Tests/conftest.py mkdtemp,
# scripts/prove_ci.sh, and various gate proofs). Append here as new
# proofs are introduced.
PATTERNS=(
  "squadvault_test_*"
  "squadvault_ci_workdb.*"
  "squadvault_fixture_state.*"
  "sv_golden_path_exports.*"
  "sv_worktree_porcelain_*"
  "sv_creative_drift_v1.*"
)

echo "SquadVault temp cleanup"
echo "  TMPDIR base : ${TMPDIR_BASE}"
echo "  age cutoff  : ${AGE_HOURS}h (${AGE_MINUTES}m)"
if [ "${DRY_RUN}" -eq 1 ]; then
  echo "  mode        : DRY RUN (no removals)"
else
  echo "  mode        : LIVE (removing matches)"
fi

before_avail="$(df -h "${TMPDIR_BASE}" | awk 'NR==2 {print $4}')"

removed_count=0

# Step 1: pattern matches directly under TMPDIR_BASE
for pattern in "${PATTERNS[@]}"; do
  while IFS= read -r -d '' dir; do
    if [ "${DRY_RUN}" -eq 1 ]; then
      echo "  [DRY] would remove: ${dir}"
    else
      rm -rf "${dir}"
      echo "  removed: ${dir}"
    fi
    removed_count=$(( removed_count + 1 ))
  done < <(find "${TMPDIR_BASE}" -maxdepth 1 -name "${pattern}" -mmin +"${AGE_MINUTES}" -print0 2>/dev/null)
done

# Step 2: pytest-of-$USER subdirectories — clean stale per-run dirs,
# preserve the parent (pytest expects it to exist on next run).
PYTEST_PARENT="${TMPDIR_BASE}/pytest-of-$(whoami)"
if [ -d "${PYTEST_PARENT}" ]; then
  while IFS= read -r -d '' dir; do
    if [ "${DRY_RUN}" -eq 1 ]; then
      echo "  [DRY] would remove: ${dir}"
    else
      rm -rf "${dir}"
      echo "  removed: ${dir}"
    fi
    removed_count=$(( removed_count + 1 ))
  done < <(find "${PYTEST_PARENT}" -mindepth 1 -maxdepth 1 -type d -mmin +"${AGE_MINUTES}" -print0 2>/dev/null)
fi

after_avail="$(df -h "${TMPDIR_BASE}" | awk 'NR==2 {print $4}')"

echo ""
echo "Summary:"
echo "  before available : ${before_avail}"
echo "  after available  : ${after_avail}"
if [ "${DRY_RUN}" -eq 1 ]; then
  echo "  candidates       : ${removed_count}"
else
  echo "  removed          : ${removed_count}"
fi
