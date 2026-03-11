#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: add Python shim compliance gate (v1) ==="

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
repo_root="$(cd -- "${here}/.." >/dev/null 2>&1 && pwd)"
cd "${repo_root}"

# Use canonical python shim
./scripts/py scripts/_patch_add_python_shim_compliance_gate_v1.py

# Ensure gate is executable (portable for bash scripts)
chmod +x scripts/check_python_shim_compliance_v1.sh

echo "==> bash syntax check"
bash -n scripts/check_python_shim_compliance_v1.sh
bash -n scripts/prove_ci.sh

echo "OK"
