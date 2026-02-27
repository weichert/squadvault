#!/bin/bash
set -euo pipefail

# Gate: Prove CI structure canonical (v1)
# - Bash 3.2 compatible
# - Never mutates repo
# - CWD-independent
#
# Enforces:
#   1) scripts/prove_ci.sh: all scripts/gate_*.sh invocations are unique
#   2) those invocations are sorted lexicographically (LC_ALL=C byte-order)
#   3) exact duplicate gate banner echo lines are disallowed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROVE_REL="scripts/prove_ci.sh"
PROVE="$REPO_ROOT/$PROVE_REL"

if [[ ! -f "$PROVE" ]]; then
  echo "ERROR: missing file: $PROVE_REL" >&2
  exit 1
fi

tmp_dir="${TMPDIR:-/tmp}"
paths_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_paths.XXXXXX")"
sorted_paths_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_paths_sorted.XXXXXX")"
dups_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_paths_dups.XXXXXX")"
banners_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_banners.XXXXXX")"
banner_dups_file="$(mktemp "$tmp_dir/sv_prove_ci_gate_banner_dups.XXXXXX")"

cleanup() {
  rm -f "$paths_file" "$sorted_paths_file" "$dups_file" "$banners_file" "$banner_dups_file"
}
trap cleanup EXIT

# Stable byte-order comparisons.
LC_ALL=C
export LC_ALL

# Extract gate invocation paths from prove_ci.sh.
# Accept:
#   bash scripts/gate_x.sh
#   bash ./scripts/gate_x.sh
#   ./scripts/gate_x.sh
#   scripts/gate_x.sh
#
# Normalize to "scripts/gate_*.sh" path token.
grep -E '(^|[[:space:]])(bash[[:space:]]+)?(\./)?scripts/gate_[^[:space:]]+\.sh([[:space:]]|$)' "$PROVE" \
  | sed -E 's/^.*\b(\.\/)?(scripts\/gate_[^[:space:]]+\.sh)\b.*$/\2/' \
  > "$paths_file" || true

# If no gates found, refuse (prove_ci always has gates).
if [[ ! -s "$paths_file" ]]; then
  echo "ERROR: no gate invocations found in $PROVE_REL" >&2
  echo "Expected at least one scripts/gate_*.sh invocation." >&2
  exit 1
fi

# 1) Uniqueness: detect duplicates.
sort "$paths_file" | uniq -d > "$dups_file" || true
if [[ -s "$dups_file" ]]; then
  echo "ERROR: duplicate gate invocations found in $PROVE_REL" >&2
  echo "" >&2
  echo "Duplicates (paths):" >&2
  sed 's/^/  - /' "$dups_file" >&2
  echo "" >&2
  echo "Hint: each scripts/gate_*.sh should be invoked exactly once in prove_ci." >&2
  exit 1
fi

# 2) Ordering: ensure the encountered sequence is already sorted.
sort "$paths_file" > "$sorted_paths_file"

# Find first out-of-order adjacent pair in the encountered sequence.
prev=""
first_bad_prev=""
first_bad_cur=""

while IFS= read -r cur; do
  if [[ -n "$prev" ]]; then
    if [[ "$prev" > "$cur" ]]; then
      first_bad_prev="$prev"
      first_bad_cur="$cur"
      break
    fi
  fi
  prev="$cur"
done < "$paths_file"

if [[ -n "$first_bad_prev" ]]; then
  echo "ERROR: gate invocations in $PROVE_REL are not sorted (lexicographic, byte-order)." >&2
  echo "" >&2
  echo "First out-of-order adjacent pair:" >&2
  echo "  - $first_bad_prev" >&2
  echo "  - $first_bad_cur" >&2
  echo "" >&2
  echo "Expected sorted order (by path):" >&2
  while IFS= read -r p; do
    echo "  - $p" >&2
  done < "$sorted_paths_file"
  echo "" >&2
  echo "Hint: reorder only the gate invocation lines (scripts/gate_*.sh) in prove_ci." >&2
  exit 1
fi

# 3) Banner duplicates: disallow exact duplicate gate banner echo lines
# (This catches accidental copy/paste of a gate banner.)
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
