#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: canonicalize patch_idempotence_allowlist_v1.txt (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_canonicalize_patch_idempotence_allowlist_v1.py

echo "==> done"
