#!/usr/bin/env bash
# SquadVault — Docs Mutation Guardrail Gate (v2)
#
# v2 hardening:
#   - Marker-based enforcement for CI index discoverability (stable to rewording).
#   - Requires exactly one canonical discoverability block for rules_of_engagement.
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

need_grep_fixed() {
  local needle="$1"
  local path="$2"
  grep -F -q -- "$needle" "$path" || fail "missing required text in $path: $needle"
}

count_fixed() {
  # prints count of fixed-string matches (as a number)
  local needle="$1"
  local path="$2"
  # grep -c exits 1 if 0 matches; normalize
  local c
  c="$(grep -F -c -- "$needle" "$path" 2>/dev/null || true)"
  echo "${c}"
}

echo "==> Docs mutation guardrail gate (v2)"

RULES_DOC="docs/process/rules_of_engagement.md"

need_file_tracked_or_present "$RULES_DOC"

# Rules-of-engagement must carry the enforced policy section (stable anchor)
need_grep_fixed "## Docs + CI Mutation Policy (Enforced)" "$RULES_DOC"
need_grep_fixed "scripts/_patch_" "$RULES_DOC"
need_grep_fixed "scripts/patch_" "$RULES_DOC"

# Removed checks (Phase 7.8 / 2dfb96e / Findings C+E retirement cluster):
#   - CI Index discoverability marker/bullet (Index simplified to gate-list-only block)
#   - scripts/_patch_example_noop_v1.{py,sh} existence (both files archived in 2dfb96e)
# The rules-of-engagement.md anchor enforcement above is the surviving real-work
# portion of this gate.

echo "OK: docs mutation guardrail gate passed (v2)."
