#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix awk portability in CI guardrails ops entrypoint parity gate (v7) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

"${PY}" scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v7.py
chmod +x scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> bash syntax check"
bash -n scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> verify awk no longer uses scalar named 'in' (best-effort)"
grep -nE "BEGIN[[:space:]]*\{[[:space:]]*in[[:space:]]*=" scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh && exit 1 || true

echo "OK"
