set -euo pipefail

echo "=== Patch: Writing Room SignalGrouping v1 (deterministic) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "repo_root: ${repo_root}"
echo "python:    ${PYTHON:-python}"
echo

echo "Step 1: apply patch"
PYTHONPATH=src "${PYTHON:-python}" scripts/_patch_writing_room_signal_grouping_v1.py

echo
echo "Step 2: run tests"
pytest
./scripts/test.sh
