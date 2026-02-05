#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: export assemblies force data selection_fingerprint (v2) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_export_assemblies_embed_real_selection_fingerprint_v2.py"

echo "==> py_compile"
python - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py", doraise=True)
print("OK: compile")
PY

echo "==> grep confirm"
grep -n "SV_PATCH_EXPORT_ASSEMBLIES_FORCE_DATA_SELECTION_FP_V2" \
  src/squadvault/consumers/recap_export_narrative_assemblies_approved.py

echo "==> next (manual, after commit):"
echo "  bash scripts/prove_ci.sh | tee /tmp/sv_prove_ci_verify.\$\$"
echo "  grep -n \"placeholder selection fingerprint detected; normalizing temp copy\" /tmp/sv_prove_ci_verify.\$\$ && echo \"ERROR\" || echo \"OK\""
echo "  rm -f /tmp/sv_prove_ci_verify.\$\$"

echo "OK"
