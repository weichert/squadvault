#!/usr/bin/env bash
set -euo pipefail
bash -n "$0"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

python -m py_compile scripts/_patch_fix_prove_ci_html_markers_creative_surface_registry_usage_v1.py
python scripts/_patch_fix_prove_ci_html_markers_creative_surface_registry_usage_v1.py

# Fail-closed: marker must not appear on an uncommented line.
# (The commented form "# <!-- ... -->" is allowed and expected.)
if grep -n -E '^[[:space:]]*[^#].*<!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_BEGIN -->' scripts/prove_ci.sh >/dev/null; then
  echo "ERROR: uncommented HTML BEGIN marker present in scripts/prove_ci.sh" >&2
  exit 1
fi
if grep -n -E '^[[:space:]]*[^#].*<!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_END -->' scripts/prove_ci.sh >/dev/null; then
  echo "ERROR: uncommented HTML END marker present in scripts/prove_ci.sh" >&2
  exit 1
fi

# Ensure bash-safe commented markers exist (at least once)
grep -n --fixed-strings "# <!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_BEGIN -->" scripts/prove_ci.sh >/dev/null
grep -n --fixed-strings "# <!-- SV_PROVE_CI_GATE_CREATIVE_SURFACE_REGISTRY_USAGE_V1_END -->" scripts/prove_ci.sh >/dev/null

bash -n scripts/prove_ci.sh
