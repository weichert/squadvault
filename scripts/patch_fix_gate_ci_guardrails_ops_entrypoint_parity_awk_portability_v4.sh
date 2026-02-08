#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: fix awk portability in CI guardrails ops entrypoint parity gate (v4) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

${PY} scripts/_patch_fix_gate_ci_guardrails_ops_entrypoint_parity_awk_portability_v4.py

echo "==> bash syntax check"
bash -n scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "==> verify awk 'in' keyword removed"
grep -nF '{in=1' scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh && exit 1 || true
grep -nE '^[[:space:]]*in[[:space:]]*\{print\}' scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh && exit 1 || true

echo "==> verify match() array form removed"
grep -nF 'match($0,' scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh && exit 1 || true

echo "==> run gate standalone"
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK"
