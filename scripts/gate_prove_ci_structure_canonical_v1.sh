#!/bin/bash
set -euo pipefail

# Gate: Prove CI structure canonical (v1)
# - Bash 3.2 compatible
# - Never mutates repo
# - CWD-independent
#
# Enforces:
#   - exact duplicate gate banner echo lines (=== Gate: ... ===) are disallowed
#     in scripts/prove_ci.sh (catches accidental copy/paste of a gate banner).
#
# Removed checks (Finding B closure, 2026-04-27):
#   1) Per-path uniqueness check.
#      Used `sed -E 's/^.*\b(...)\b.*$/\1/'` for path extraction. macOS BSD
#      sed treats `\b` as literal, silently passing through full lines instead
#      of extracted path tokens — gate became a no-op on Mac for years.
#      Even with regex fixed, the check's "exactly once" invariant is
#      structurally incompatible with stateful gates like
#      gate_worktree_cleanliness_v1.sh whose begin/assert/end contract
#      requires multiple invocations. False-positives on Linux, false-
#      negatives on Mac. Both directions broken; check removed rather than
#      patched with an exception list.
#   2) Per-path lexicographic-order check. Same path extraction as #1, same
#      portability bug. Even if extraction worked, the worktree_cleanliness
#      pattern intersperses the same path between unrelated invocations,
#      defeating the linear-sort invariant.
#
# The banner-uniqueness check below is the surviving real-work portion of
# this gate. Banner extraction uses grep against literal `=== Gate: ... ===`
# patterns — no regex word-boundary issues, fully portable.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROVE_REL="scripts/prove_ci.sh"
PROVE="$REPO_ROOT/$PROVE_REL"

if [[ ! -f "$PROVE" ]]; then
  echo "ERROR: missing file: $PROVE_REL" >&2
  exit 1
fi

tmp_dir="${TMPDIR:-/tmp}"
banners_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_banners.XXXXXX")"
banner_dups_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_banner_dups.XXXXXX")"

cleanup() {
  rm -f "$banners_file" "$banner_dups_file"
}
trap cleanup EXIT

# Stable byte-order comparisons.
LC_ALL=C
export LC_ALL

# Banner duplicates: disallow exact duplicate gate banner echo lines
# (catches accidental copy/paste of a gate banner).
grep -E '^\s*echo\s+["'\''"]===\s*Gate:\s*.*===["'\''"]\s*$' "$PROVE" > "$banners_file" || true
if [[ -s "$banners_file" ]]; then
  sort "$banners_file" | uniq -d > "$banner_dups_file" || true
  if [[ -s "$banner_dups_file" ]]; then
    echo "ERROR: duplicate gate banner echo lines found in $PROVE_REL" >&2
    echo "" >&2
    echo "Duplicate banner lines:" >&2
    sed 's/^/  /' "$banner_dups_file" >&2
    echo "" >&2
    echo "Hint: each '=== Gate:' banner line should appear at most once." >&2
    exit 1
  fi
fi

exit 0
