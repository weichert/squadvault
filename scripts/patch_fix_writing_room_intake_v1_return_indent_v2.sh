#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix WR intake_v1 column-0 return indentation (v2) ==="
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "repo_root: ${repo_root}"
echo "python:    ${PYTHON:-python}"
echo

echo "Step 1: apply patch"
PYTHONPATH=src "${PYTHON:-python}" scripts/_patch_fix_writing_room_intake_v1_return_indent_v2.py

echo
echo "Step 2: compile check"
python -m py_compile src/squadvault/recaps/writing_room/intake_v1.py

echo
echo "Step 3: run tests"
pytest
./scripts/test.sh
