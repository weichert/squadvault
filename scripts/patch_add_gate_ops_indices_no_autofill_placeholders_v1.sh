#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add ops indices no-autofill placeholders gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_add_gate_ops_indices_no_autofill_placeholders_v1.py

echo "==> ensure executable bit"
chmod +x scripts/gate_ops_indices_no_autofill_placeholders_v1.sh

echo "==> bash syntax check (gate)"
bash -n scripts/gate_ops_indices_no_autofill_placeholders_v1.sh

echo "OK"
