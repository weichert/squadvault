#!/bin/bash
set -euo pipefail

# Gate: enforce canonical ordering of CI_PROOF_RUNNERS bounded block entries.
# - Bash 3.2 compatible (no mapfile/readarray)
# - Never mutates repo
# - CWD-independent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

DOC_REL="docs/80_indices/ops/CI_Proof_Surface_Registry_v1.0.md"
DOC="$REPO_ROOT/$DOC_REL"

BEGIN="<!-- CI_PROOF_RUNNERS_BEGIN -->"
END="<!-- CI_PROOF_RUNNERS_END -->"

if [[ ! -f "$DOC" ]]; then
  echo "ERROR: missing doc: $DOC_REL" >&2
  exit 1
fi

tmp_dir="${TMPDIR:-/tmp}"
block_file="$(mktemp "$tmp_dir/sv_ci_proof_runners_block.XXXXXX")"
bullets_file="$(mktemp "$tmp_dir/sv_ci_proof_runners_bullets.XXXXXX")"
paths_file="$(mktemp "$tmp_dir/sv_ci_proof_runners_paths.XXXXXX")"
sorted_paths_file="$(mktemp "$tmp_dir/sv_ci_proof_runners_paths_sorted.XXXXXX")"

cleanup() {
  rm -f "$block_file" "$bullets_file" "$paths_file" "$sorted_paths_file"
}
trap cleanup EXIT

# Extract the bounded block (exclusive of BEGIN/END lines).
# If markers are missing/misordered, fail loudly.
awk -v b="$BEGIN" -v e="$END" '
  $0 == b {inblk=1; next}
  $0 == e {exit}
  inblk {print}
' "$DOC" > "$block_file"

if ! grep -Fqx "$BEGIN" "$DOC" || ! grep -Fqx "$END" "$DOC"; then
  echo "ERROR: missing bounded block markers in $DOC_REL" >&2
  echo "Expected to find exact lines:" >&2
  echo "  $BEGIN" >&2
  echo "  $END" >&2
  exit 1
fi

# Ensure END occurs after BEGIN (simple structural sanity).
# (We do this by verifying the BEGIN line number < END line number.)
begin_ln="$(grep -n -F "$BEGIN" "$DOC" | head -n 1 | sed -E 's/:.*$//')"
end_ln="$(grep -n -F "$END" "$DOC" | head -n 1 | sed -E 's/:.*$//')"
if [[ -z "$begin_ln" || -z "$end_ln" || "$begin_ln" -ge "$end_ln" ]]; then
  echo "ERROR: bounded block markers misordered in $DOC_REL" >&2
  echo "BEGIN line: $begin_ln" >&2
  echo "END line:   $end_ln" >&2
  exit 1
fi

# Extract bullet lines beginning with "- scripts/" (allow leading whitespace).
# Preserve the original bullet lines for diagnostics, but ordering compares by script path.
grep -E '^[[:space:]]*-[[:space:]]*scripts/' "$block_file" > "$bullets_file" || true

# If there are zero bullets, that's structurally weird but not necessarily a sorting failure.
# We'll treat as pass (nothing to order).
if [[ ! -s "$bullets_file" ]]; then
  exit 0
fi

# Extract just the script paths (scripts/...) up to first whitespace.
# Note: we only enforce ordering by the path token.
sed -E 's/^[[:space:]]*-[[:space:]]*(scripts\/[^[:space:]]*).*$/\1/' "$bullets_file" > "$paths_file"

# Verify lexicographic (byte-order) ordering in the current sequence.
# Set locale to C for stable byte-order comparisons.
LC_ALL=C
export LC_ALL

prev=""
first_bad_prev=""
first_bad_cur=""

# bash 3.2-safe line iteration
while IFS= read -r cur; do
  if [[ -n "$prev" ]]; then
    # If prev > cur, we found the first out-of-order adjacent pair.
    if [[ "$prev" > "$cur" ]]; then
      first_bad_prev="$prev"
      first_bad_cur="$cur"
      break
    fi
  fi
  prev="$cur"
done < "$paths_file"

if [[ -z "$first_bad_prev" ]]; then
  exit 0
fi

# Build expected sorted order (stable, byte-order).
sort "$paths_file" > "$sorted_paths_file"

echo "ERROR: CI_PROOF_RUNNERS block bullet entries are not sorted (lexicographic, byte-order)." >&2
echo "Doc: $DOC_REL" >&2
echo "" >&2
echo "First out-of-order adjacent pair:" >&2
echo "  - $first_bad_prev" >&2
echo "  - $first_bad_cur" >&2
echo "" >&2
echo "Expected sorted order for bullet entries (by script path):" >&2
# Print as bullets (no extra reformatting beyond listing)
while IFS= read -r p; do
  echo "  - $p" >&2
done < "$sorted_paths_file"
echo "" >&2
echo "Hint: reorder only the '- scripts/...' bullet entries inside the bounded block; comments/blank lines may remain." >&2
exit 1
