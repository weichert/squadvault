#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PY_BIN="${PY_BIN:-}"

# Choose a Python that has pytest installed.
# Order: $PY_BIN (if provided) -> python -> python3 -> fall back to pytest executable.
if [[ -n "${PY_BIN}" ]]; then
  if ! "${PY_BIN}" -c "import pytest" >/dev/null 2>&1; then
    echo "ERROR: PY_BIN is set to ${PY_BIN} but pytest is not installed in that interpreter." >&2
    exit 2
  fi
else
  if python -c "import pytest" >/dev/null 2>&1; then
    PY_BIN="python"
  elif python3 -c "import pytest" >/dev/null 2>&1; then
    PY_BIN="python3"
  else
    PY_BIN=""
  fi
fi


echo "=== Patch: Writing Room intake_v1 exclusions (schema-aligned) ==="
echo "repo_root: $ROOT"
echo "python:    $PY_BIN"
echo


echo "Step 1: patch intake_v1 ExcludedSignal(details=...)"
"$PY_BIN" scripts/_patch_intake_v1_excluded_signal_details.py

echo
export PYTHONPATH="$ROOT:$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
pytest -q
