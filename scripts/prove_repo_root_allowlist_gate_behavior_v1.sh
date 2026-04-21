#!/usr/bin/env bash
# SquadVault — proof: repo-root allowlist gate behavior (v1)
#
# What this proves:
#  1) The gate FAILS when a file at repo root is outside ALLOWED_ROOT_FILES.
#  2) The gate PASSES when only allowlisted files are present at repo root.
#
# Notes:
#  - Tests/test_repo_root_allowlist_v1.py scans Path.iterdir() of the repo
#    root, so tracking status is irrelevant — the probe file only needs to
#    exist in the working tree to trigger a failure.
#  - No escape-hatch case: the gate has no gate-level escape hatch. The
#    pre-commit hook's SV_SKIP_PRECOMMIT=1 hatch is tested separately.
#
# Determinism:
#  - Requires clean repo at entry.
#  - Writes a probe file at repo root, runs gate, then fully cleans up.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: proof requires clean repo (working tree + index)."
  git status --porcelain=v1
  exit 2
fi

PROBE="sv_repo_root_allowlist_probe_v1.tmp"

cleanup() {
  set +e
  rm -f "${PROBE}"
  set -e
}
trap cleanup EXIT

# --- Case 1: gate should FAIL when a non-allowlisted file is at repo root ---
: > "${PROBE}"

set +e
out="$(bash scripts/gate_repo_root_allowlist_v1.sh 2>&1)"
rc=$?
set -e

if [[ $rc -eq 0 ]]; then
  echo "ERROR: expected gate to fail when non-allowlisted file is at repo root."
  echo "${out}"
  exit 1
fi

rm -f "${PROBE}"

# --- Case 2: gate should PASS on a clean tree ---
bash scripts/gate_repo_root_allowlist_v1.sh >/dev/null

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "ERROR: proof left repo dirty unexpectedly."
  git status --porcelain=v1
  exit 1
fi

echo "OK: repo-root allowlist gate behavior proved (v1)."
