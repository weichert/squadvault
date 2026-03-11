#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PATCHER="scripts/_patch_gen_creative_surface_fingerprint_scope_v1.py"
GEN="scripts/gen_creative_surface_fingerprint_v1.py"

./scripts/py -m py_compile "$PATCHER"
./scripts/py "$PATCHER"

# Sanity: marker + allowlist function must be present
grep -n --fixed-string "SV_CREATIVE_SURFACE_SCOPE_V1" "$GEN" >/dev/null
grep -n --fixed-string "_sv_is_allowed_creative_surface_path_v1" "$GEN" >/dev/null

# Sanity: ensure we applied the filter (either supported shape)
if grep -n --fixed-string "sorted(p for p in _git_ls_files() if _sv_is_allowed_creative_surface_path_v1(p))" "$GEN" >/dev/null; then
  :
elif grep -n --fixed-string "_sv_is_allowed_creative_surface_path_v1(p)" "$GEN" >/dev/null; then
  # Accept alternative patch shape (inline ls-files splitlines)
  :
else
  echo "ERROR: expected allowlist application in $GEN but did not find it" >&2
  exit 2
fi

bash -n "$0"

echo "OK: wrap_patch_gen_creative_surface_fingerprint_scope_v1"
