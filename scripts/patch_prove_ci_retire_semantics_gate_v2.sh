#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: prove_ci retire semantics gate (v2) ==="

repo_root="$(git rev-parse --show-toplevel)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_prove_ci_retire_semantics_gate_v2.py"

echo "==> bash -n"
bash -n "${repo_root}/scripts/prove_ci.sh"
echo "OK"
