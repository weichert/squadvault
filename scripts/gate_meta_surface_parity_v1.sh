#!/usr/bin/env bash
set -euo pipefail

# Gate: meta surface parity (v1)
# - Aggregates and fails fast on:
#   - proof surface registry exactness
#   - CI registry ↔ execution alignment
#   - CI guardrails ops entrypoint parity
#   - patcher/wrapper pairing
#
# NOTE: Each underlying gate is already best-in-class. This just makes them an explicit "meta" surface.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

echo "==> meta: patcher/wrapper pairing"
bash scripts/check_patch_pairs_v1.sh

echo "==> meta: proof surface registry exactness"
bash scripts/gate_proof_suite_completeness_v1.sh

echo "==> meta: CI registry ↔ execution alignment"
bash scripts/gate_ci_registry_execution_alignment_v1.sh

echo "==> meta: CI guardrails ops entrypoint parity"
bash scripts/gate_ci_guardrails_ops_entrypoint_parity_v1.sh

echo "OK: meta surface parity passed (v1)"
exit 0
