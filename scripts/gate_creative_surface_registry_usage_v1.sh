#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

bash scripts/gate_creative_surface_registry_discoverability_v1.sh

registry_doc="docs/80_indices/ops/Creative_Surface_Registry_v1.0.md"
if [ ! -f "$registry_doc" ]; then
  echo "ERROR: registry doc missing: $registry_doc" >&2
  exit 1
fi

registered_ids_raw="$(grep -h -o -E 'CREATIVE_SURFACE_[A-Z0-9_]+' "$registry_doc" || true)"
registered_ids="$(printf "%s\n" "$registered_ids_raw" | sed '/^$/d' | sort -u)"
if [ -z "$registered_ids" ]; then
  echo "ERROR: no CREATIVE_SURFACE_* tokens found in registry doc" >&2
  exit 1
fi

reg_total="$(printf "%s\n" "$registered_ids_raw" | sed '/^$/d' | wc -l | tr -d ' ')"
reg_unique="$(printf "%s\n" "$registered_ids" | wc -l | tr -d ' ')"
if [ "$reg_total" != "$reg_unique" ]; then
  echo "ERROR: duplicate CREATIVE_SURFACE_* tokens in registry doc" >&2
  exit 1
fi

usage_raw="$(
  git grep -h -o -E 'CREATIVE_SURFACE_[A-Z0-9_]+' -- . \
    ':!**/docs/80_indices/ops/Creative_Surface_Registry_v1.0.md' \
    ':!**/artifacts/CREATIVE_SURFACE_FINGERPRINT_v1.json' \
  | sort -u || true
)"

# Filter out non-surface tokens (gate markers, script identifiers, registry meta)
usage_ids="$(
  printf "%s\n" "$usage_raw" \
    | grep -v -E '(_BEGIN|_END)$' \
    | grep -v -E '_GATE_' \
    | grep -v -E 'CREATIVE_SURFACE_REGISTRY$' \
    | grep -v -E '_$' \
    | sed '/^$/d' \
    | sort -u || true
)"

if [ -z "$usage_ids" ]; then
  exit 0
fi

missing="$(
  comm -23 \
    <(printf "%s\n" "$usage_ids" | sort -u) \
    <(printf "%s\n" "$registered_ids" | sort -u) || true
)"

if [ -n "$missing" ]; then
  echo "ERROR: Creative Surface IDs referenced but not registered in registry doc:" >&2
  printf "%s\n" "$missing" | sed 's/^/ - /' >&2
  exit 1
fi

exit 0
