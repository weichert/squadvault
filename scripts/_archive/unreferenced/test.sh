#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

# Prefer an env python that has pytest installed.
if python -c "import pytest" >/dev/null 2>&1; then
  PY=python
elif python3 -c "import pytest" >/dev/null 2>&1; then
  PY=python3
else
  echo "ERROR: pytest not installed in python/python3 environment." >&2
  exit 2
fi

echo "=== SquadVault: tests ==="
echo "repo_root: $ROOT"
echo "python:    $PY"
echo

"$PY" -m pytest -q
