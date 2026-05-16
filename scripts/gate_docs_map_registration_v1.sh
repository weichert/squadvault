#!/usr/bin/env bash
# SquadVault -- gate: docs/ top-level files must be accompanied by a Map touch (v1)
#
# Purpose:
#   Fail if any new top-level file is staged under docs/ without a Documentation
#   Map modification or patch addendum staged in the same set. Enforces Reset
#   Memo v1.0 section 6.3: a binding document is not binding until registered in
#   the Map; authoring a binding document ships in two commits (document, then
#   Map update) or in one commit where both are staged together.
#
# Scope:
#   - New files (--diff-filter=A) directly in docs/ (not in subdirectories).
#   - Map files matched by: docs/SquadVault_Documentation_Map_v*.{md,docx}
#   - Patch addenda matched by: docs/map_patch_*.md
#   - Extensions checked: .md, .docx, .pdf
#   - Subdirectory additions (docs/templates/, docs/80_indices/, etc.) are NOT
#     caught -- those are support artifacts, not top-level binding doctrine.
#
# Escape hatch:
#   None at the gate level. The pre-commit hook's SV_SKIP_PRECOMMIT=1 hatch
#   applies to the entire hook chain, which includes this gate.
#   For provisional docs that belong in _observations/ not docs/, use that path
#   instead; the gate does not fire on _observations/ additions.
#
# Determinism / Safety:
#   - repo-root anchored
#   - no network, no package installs, no xtrace
#   - bash3-safe

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "==> docs/ Map registration gate"

# --- New top-level docs/ files in the staging set ---
staged_new="$(git diff --cached --name-only --diff-filter=A 2>/dev/null || true)"

# Files directly in docs/ (not in a subdirectory) with binding-doc extensions.
new_docs_top="$(printf '%s\n' "${staged_new}" \
  | grep -E '^docs/[^/]+\.(md|docx|pdf)$' \
  || true)"

if [[ -z "${new_docs_top}" ]]; then
  echo "OK: no new top-level docs/ files staged."
  exit 0
fi

# --- Check for Map or patch addendum in full staging set ---
staged_all="$(git diff --cached --name-only 2>/dev/null || true)"

map_or_patch="$(printf '%s\n' "${staged_all}" \
  | grep -E '^docs/(SquadVault_Documentation_Map_v|map_patch_)' \
  || true)"

if [[ -n "${map_or_patch}" ]]; then
  echo "OK: new docs/ top-level file(s) accompanied by Map or patch addendum."
  exit 0
fi

# --- Failure ---
echo "ERROR: New top-level docs/ file(s) staged without a Documentation Map" >&2
echo "       modification or patch addendum in the same commit." >&2
echo "" >&2
echo "  New file(s):" >&2
printf '%s\n' "${new_docs_top}" | sed 's/^/    /' >&2
echo "" >&2
echo "  Fix options:" >&2
echo "    1. Stage a Map version (docs/SquadVault_Documentation_Map_v*.md) or" >&2
echo "       patch addendum (docs/map_patch_*.md) in the same commit." >&2
echo "    2. If this document is provisional (not yet binding), file it in" >&2
echo "       _observations/ instead of docs/." >&2
echo "" >&2
echo "  Per Reset Memo v1.0 section 6.3." >&2
exit 1
