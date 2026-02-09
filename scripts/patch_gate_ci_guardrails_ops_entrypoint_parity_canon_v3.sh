#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: canonicalize ops entrypoint parity gate detection (v3) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_gate_ci_guardrails_ops_entrypoint_parity_canon_v3.py
chmod +x scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> bash syntax check"
bash -n scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> smoke: run parity gate standalone"
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK"
