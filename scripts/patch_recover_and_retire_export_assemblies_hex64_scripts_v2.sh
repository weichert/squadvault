#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: recover + retire export-assemblies HEX64 scripts (v2) ==="

repo_root="$(git rev-parse --show-toplevel)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_recover_and_retire_export_assemblies_hex64_scripts_v2.py"

echo "==> list retired dir"
ls -la "${repo_root}/scripts/_retired/export_assemblies_hex64" || true
echo "OK"
