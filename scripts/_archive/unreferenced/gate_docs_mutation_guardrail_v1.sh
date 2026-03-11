#!/usr/bin/env bash
# NOTE (v1 deprecation):
#   This gate is superseded by:
#     scripts/gate_docs_mutation_guardrail_v2.sh
#   Kept for historical reference only. prove_ci wires v2.
#
# SquadVault — Docs Mutation Guardrail Gate (v1)
#
# Enforces:
#   1) Docs mutation policy is discoverable + present in canonical docs.
#   2) Docs indices remain consistent (key references present).
#   3) Canonical patcher/wrapper workflow artifacts exist (examples/templates).
#
# Constraints:
#   - bash3-safe (no mapfile)
#   - deterministic
#   - does NOT depend on git dirty/clean state
#   - uses git ls-files for tracked enumeration (when applicable)
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
  # Prefer git-tracked check when inside a git worktree.
  # If git isn't available, fall back to filesystem presence.
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

echo "==> Docs mutation guardrail gate (v1)"

# --- Canonical docs targets (must exist) ---
RULES_DOC="docs/process/rules_of_engagement.md"
CI_INDEX_DOC="docs/80_indices/ops/CI_Guardrails_Index_v1.0.md"

need_file_tracked_or_present "$RULES_DOC"
need_file_tracked_or_present "$CI_INDEX_DOC"

# --- Enforce: rules-of-engagement contains the enforced docs mutation policy block ---
need_grep_fixed "## Docs + CI Mutation Policy (Enforced)" "$RULES_DOC"
need_grep_fixed "versioned patcher" "$RULES_DOC"
need_grep_fixed "scripts/_patch_" "$RULES_DOC"
need_grep_fixed "scripts/patch_" "$RULES_DOC"

# --- Enforce: CI guardrails index references docs mutation policy / rules-of-engagement ---
# Keep this intentionally tolerant: ensure discoverability without requiring exact link formatting.
need_grep_fixed "rules_of_engagement" "$CI_INDEX_DOC"
need_grep_fixed "Docs + CI Mutation Policy" "$CI_INDEX_DOC"

# --- Enforce: canonical patcher/wrapper examples exist (discoverable proof that workflow exists) ---
# These names are grounded in your current repo state (example noop patch) and are stable.
need_file_tracked_or_present "scripts/_patch_example_noop_v1.py"
need_file_tracked_or_present "scripts/patch_example_noop_v1.sh"

# Optional-but-recommended: template presence (do not hard-fail if absent; emit note under SV_DEBUG)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files "scripts/_patch_template"* "scripts/patch_template"* >/dev/null 2>&1; then
    : # present (no-op)
  else
    if [[ "${SV_DEBUG:-0}" == "1" ]]; then
      echo "NOTE: template patcher/wrapper not detected via git ls-files; examples cover workflow." >&2
    fi
  fi
fi

echo "OK: docs mutation guardrail gate passed."
