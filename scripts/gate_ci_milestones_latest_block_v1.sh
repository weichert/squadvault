#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)"

DOC="$REPO_ROOT/docs/logs/CI_MILESTONES.md"

BEGIN="<!-- SV_CI_MILESTONES_LATEST_v1_BEGIN -->"
END="<!-- SV_CI_MILESTONES_LATEST_v1_END -->"

if [ ! -f "$DOC" ]; then
  echo "ERR: missing file: $DOC" >&2
  exit 1
fi

b_ct="$(grep -Fxc "$BEGIN" "$DOC" || true)"
e_ct="$(grep -Fxc "$END" "$DOC" || true)"

if [ "$b_ct" != "$e_ct" ]; then
  echo "ERR: Latest marker count mismatch: BEGIN=$b_ct END=$e_ct" >&2
  exit 1
fi

if [ "$b_ct" -ne 1 ]; then
  echo "ERR: Latest bounded block must exist exactly once: found $b_ct" >&2
  exit 1
fi

b_ln="$(grep -Fn "$BEGIN" "$DOC" | head -n 1 | cut -d: -f1)"
e_ln="$(grep -Fn "$END"   "$DOC" | head -n 1 | cut -d: -f1)"

if [ -z "${b_ln:-}" ] || [ -z "${e_ln:-}" ]; then
  echo "ERR: Latest marker lines not found (unexpected)" >&2
  exit 1
fi

# numeric compare
if [ "$b_ln" -ge "$e_ln" ]; then
  echo "ERR: Latest markers out of order: BEGIN line=$b_ln END line=$e_ln" >&2
  exit 1
fi

exit 0
