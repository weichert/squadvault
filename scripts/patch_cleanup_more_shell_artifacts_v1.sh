#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: cleanup more accidental shell artifact files (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_cleanup_more_shell_artifacts_v1.py
echo "OK"
