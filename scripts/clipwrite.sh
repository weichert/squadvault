#!/usr/bin/env bash
set -euo pipefail
PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then PY="${PYTHON:-python}"; fi
exec "${PY}" scripts/clipwrite.py "$@"
