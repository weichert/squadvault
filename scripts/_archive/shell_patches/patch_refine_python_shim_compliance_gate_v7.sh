#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: shim gate boundary includes ':' (robust v7) ==="

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
repo_root="$(cd -- "${here}/.." >/dev/null 2>&1 && pwd)"
cd "${repo_root}"

./scripts/py scripts/_patch_refine_python_shim_compliance_gate_v7.py

echo "==> bash syntax check"
bash -n scripts/check_python_shim_compliance_v2.sh

echo "OK"
