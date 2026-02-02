#!/usr/bin/env bash
set -euo pipefail

# CWD-independent: resolve repo root relative to this script
here="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"

python_bin="${PYTHON:-python}"

echo "==> Docs integrity gate (v1)"
"$python_bin" "$repo_root/scripts/check_docs_integrity_v1.py"
echo "OK: docs integrity gate (v1) passed"
