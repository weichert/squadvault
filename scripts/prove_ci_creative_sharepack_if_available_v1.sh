#!/usr/bin/env bash
set -euo pipefail

# CWD independence
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
cd "${repo_root}"

echo "=== Proof (CI): creative sharepack determinism if inputs present (v1) ==="

# Find an approved export (first match, stable ordering).
approved_path="$(
  find artifacts/exports -type f \( -name '*__approved_*.md' -o -name '*_approved_*.md' \) 2>/dev/null \
  | LC_ALL=C sort \
  | head -n 1 \
  || true
)"

if [[ -z "${approved_path}" ]]; then
  echo "SKIP: no approved exports found under artifacts/exports (creative sharepack determinism not applicable)."
  exit 0
fi

# Expected shape: artifacts/exports/<league>/<season>/week_<NN>/<file>.md
# Extract league, season, and week NN.
league_id="$(printf "%s" "${approved_path}" | sed -E 's|^artifacts/exports/([^/]+)/.*$|\1|')"
season="$(printf "%s" "${approved_path}" | sed -E 's|^artifacts/exports/[^/]+/([^/]+)/.*$|\1|')"
week_nn="$(printf "%s" "${approved_path}" | sed -E 's|^artifacts/exports/[^/]+/[^/]+/week_([0-9]{2})/.*$|\1|')"

if [[ -z "${league_id}" || -z "${season}" || -z "${week_nn}" || "${week_nn}" == "${approved_path}" ]]; then
  echo "ERROR: could not derive league/season/week from approved export path:"
  echo "  ${approved_path}"
  exit 1
fi

# Convert week_nn -> integer week_index (strip leading zero safely).
week_index="$((10#${week_nn}))"

echo "Found approved export:"
echo "  path=${approved_path}"
echo "  league_id=${league_id} season=${season} week_index=${week_index}"

export SV_LEAGUE_ID="${league_id}"
export SV_SEASON="${season}"
export SV_WEEK_INDEX="${week_index}"

bash scripts/prove_creative_sharepack_determinism_v1.sh

echo "OK"
