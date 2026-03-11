#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index Paste-Safe File Writes in rules_of_engagement.md (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

exec "${PY}" scripts/_patch_rules_of_engagement_add_paste_safe_writes_v1.py
