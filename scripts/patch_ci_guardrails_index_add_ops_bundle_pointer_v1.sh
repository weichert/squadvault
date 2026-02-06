#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: CI Guardrails Index add ops bundle pointer (v1) ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

python="${PYTHON:-python}"
./scripts/py scripts/_patch_ci_guardrails_index_add_ops_bundle_pointer_v1.py

echo "==> done"
