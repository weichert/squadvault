#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: register terminal banner proof runner in CI proof registry (v2) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_register_terminal_banner_proof_runner_in_ci_registry_v2.py"
REGISTRY="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> sanity: ensure registry now contains entry"
grep -nF "scripts/prove_no_terminal_banner_paste_gate_behavior_v1.sh" "${REGISTRY}"

echo "OK"
