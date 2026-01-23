#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: WR intake_v1 wire-up SignalGrouping v1 (v3) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "repo_root: ${repo_root}"
echo "python:    ${PYTHON:-python}"
echo

echo "Step 1: apply patch"
PYTHONPATH=src "${PYTHON:-python}" scripts/_patch_writing_room_signal_grouping_v1_intake_fix_v3.py

echo
echo "Step 2: run tests"
pytest
./scripts/test.sh
