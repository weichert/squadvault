#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PY_BIN="${PY_BIN:-python}"

echo "=== SquadVault: Add/Refresh Pytest Bootstrap ==="
echo "repo_root: $ROOT"
echo "python:    $PY_BIN"
echo

PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" "$PY_BIN" scripts/_patch_pytest_import_paths_repo_root_and_src.py

echo
echo "Done. Verify with:"
echo "  pytest -q"
echo "  ./scripts/test.sh"
