#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: export assemblies define HEX64_RE locally in main (v5) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_export_assemblies_define_hex64_re_local_v5.py"

echo "==> py_compile"
python -m py_compile src/squadvault/consumers/recap_export_narrative_assemblies_approved.py
echo "OK: compile"

echo "==> grep confirm"
git grep -n -- "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_LOCAL_V5" -- src/squadvault/consumers/recap_export_narrative_assemblies_approved.py
echo "OK"
