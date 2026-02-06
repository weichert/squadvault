#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: export assemblies remove HEX64_RE v4 artifact lines (v6) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_export_assemblies_remove_hex64_re_v4_artifact_v6.py"

echo "==> py_compile"
python -m py_compile src/squadvault/consumers/recap_export_narrative_assemblies_approved.py
echo "OK: compile"

echo "==> grep confirm (v4 artifact should be absent; v5 local marker should remain)"
grep -n "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_V4" -n src/squadvault/consumers/recap_export_narrative_assemblies_approved.py && {
  echo "ERROR: v4 marker still present"
  exit 1
} || true

grep -n "SV_PATCH_EXPORT_ASSEMBLIES_DEFINE_HEX64_RE_LOCAL_V5" -n src/squadvault/consumers/recap_export_narrative_assemblies_approved.py >/dev/null
echo "OK"
