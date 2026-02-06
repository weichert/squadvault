#!/usr/bin/env bash
set -euo pipefail

echo "=== Patch: export assemblies embed real selection_fingerprint (v1) ==="

# bash3-safe repo_root resolution
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
py="${repo_root}/scripts/py"

"${repo_root}/scripts/py" "${repo_root}/scripts/_patch_export_assemblies_embed_real_selection_fingerprint_v1.py"

echo "==> py_compile"
python - <<'PY'
import py_compile
py_compile.compile("src/squadvault/consumers/recap_export_narrative_assemblies_approved.py", doraise=True)
print("OK: compile")
PY

echo "==> prove_ci (and assert NAC preflight normalization line is gone)"
out="/tmp/sv_prove_ci_out.$$"
bash "${repo_root}/scripts/prove_ci.sh" | tee "${out}"

if grep -n "placeholder selection fingerprint detected; normalizing temp copy" "${out}" >/dev/null 2>&1; then
  echo "ERROR: NAC preflight normalization message still present (expected removed)." >&2
  rm -f "${out}"
  exit 1
fi

rm -f "${out}"
echo "OK"
