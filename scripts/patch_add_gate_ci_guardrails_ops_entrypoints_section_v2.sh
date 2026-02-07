#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add gate_ci_guardrails_ops_entrypoints_section_v2.sh (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_add_gate_ci_guardrails_ops_entrypoints_section_v2.py

chmod +x scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh

echo "==> bash syntax check"
bash -n scripts/gate_ci_guardrails_ops_entrypoints_section_v2.sh

echo "OK"
