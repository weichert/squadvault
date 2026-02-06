#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: export assemblies define HEX64_RE (v4) ==="

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"$py" "${repo_root}/scripts/_patch_export_assemblies_define_hex64_re_v4.py"

echo "==> py_compile"
python -m py_compile src/squadvault/consumers/recap_export_narrative_assemblies_approved.py
echo "OK: compile"

echo "==> next (manual, after commit):"
cat <<'NEXT'
  bash scripts/prove_ci.sh | tee /tmp/sv_prove_ci_verify.$$
  grep -n "NameError: name 'HEX64_RE' is not defined" /tmp/sv_prove_ci_verify.$$ && echo "ERROR" || echo "OK: HEX64_RE fixed"
  rm -f /tmp/sv_prove_ci_verify.$$
NEXT
