#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: prove_ci add no double scripts prefix gate (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# Ensure the gate exists (canonical path)
test -f scripts/gate_no_double_scripts_prefix_v1.sh

SV_DOCS_GATES_INSERT_LABEL="no double scripts prefix (v1)" \
SV_DOCS_GATES_INSERT_PATH="scripts/gate_no_double_scripts_prefix_v1.sh" \
bash scripts/patch_prove_ci_insert_under_docs_gates_anchor_v2.sh

echo "==> Verify: prove_ci references the new gate"
grep -nF "bash scripts/gate_no_double_scripts_prefix_v1.sh" scripts/prove_ci.sh >/dev/null

echo "==> bash syntax check"
bash -n scripts/prove_ci.sh
bash -n scripts/patch_prove_ci_add_no_double_scripts_prefix_gate_v1.sh

echo "OK"
