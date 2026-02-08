#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: index terminal banner proof runner discoverability (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

PATCHER="scripts/_patch_index_terminal_banner_proof_runner_discoverability_v1.py"
DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

PY="./scripts/py"
if [[ ! -x "${PY}" ]]; then
  PY="${PYTHON:-python}"
fi

echo "==> run patcher"
${PY} "${PATCHER}"

echo "==> grep confirm (context)"
grep -n -C 3 "prove_no_terminal_banner_paste_gate_behavior_v1.sh" "${DOC}" || true

echo "OK"
