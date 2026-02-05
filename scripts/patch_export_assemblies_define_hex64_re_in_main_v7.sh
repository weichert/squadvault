#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: export assemblies define HEX64_RE at top of main (v7) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_export_assemblies_define_hex64_re_in_main_v7.py"

echo "==> py_compile"
python -m py_compile src/squadvault/consumers/recap_export_narrative_assemblies_approved.py
echo "OK: compile"

echo "==> grep confirm"
grep -n "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_IN_MAIN_V7" src/squadvault/consumers/recap_export_narrative_assemblies_approved.py
echo "OK"
