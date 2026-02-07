#!/usr/bin/env bash
# SquadVault — Docs Integrity Gate (v2)
#
# v2 = existing docs integrity proof + marker exact-once enforcement (folded).
#
# Constraints:
#   - bash3-safe
#   - deterministic
#   - does NOT depend on git dirty/clean state
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

need_file_tracked_or_present() {
  local path="$1"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git ls-files --error-unmatch "$path" >/dev/null 2>&1 || fail "required tracked file missing: $path"
  else
    [[ -f "$path" ]] || fail "required file missing (no git): $path"
  fi
}

count_fixed() {
  local needle="$1"
  local path="$2"
  local c
  c="$(grep -F -c -- "$needle" "$path" 2>/dev/null || true)"
  echo "${c}"
}

echo "==> Docs integrity gate (v2)"

# 1) Baseline docs integrity proof
bash "scripts/prove_docs_integrity_v1.sh"

# 2) Marker exact-once enforcement (folded from docs_integrity_markers gate v2)
CI_INDEX="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"
need_file_tracked_or_present "$CI_INDEX"

m1="<!-- SV_DOCS_MUTATION_DISCOVERABILITY: rules_of_engagement (v1) -->"
m2="<!-- SV_DOCS_MUTATION_GUARDRAIL_GATE: v2 (v1) -->"

c1="$(count_fixed "$m1" "$CI_INDEX")"
c2="$(count_fixed "$m2" "$CI_INDEX")"

[[ "$c1" == "1" ]] || fail "marker must appear exactly once (found $c1): $m1"
[[ "$c2" == "1" ]] || fail "marker must appear exactly once (found $c2): $m2"

echo "OK: docs integrity gate passed (v2)."
