#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: export assemblies fingerprint block uses approved.selection_fingerprint (v3) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_export_assemblies_use_approved_fp_for_fingerprint_block_v3.py"

echo "==> py_compile"
"$py" - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py", doraise=True)
print("OK: compile")
PY

echo "==> prove_ci (verify NAC preflight line is gone)"
tmp="/tmp/sv_prove_ci_verify.$$"
SV_KEEP_EXPORT_TMP=1 bash scripts/prove_ci.sh | tee "$tmp"
if grep -n "placeholder selection fingerprint detected; normalizing temp copy" "$tmp"; then
  echo "ERROR: NAC preflight normalization still present" >&2
  rm -f "$tmp"
  exit 1
fi
rm -f "$tmp"
echo "OK"
