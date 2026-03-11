from __future__ import annotations

from pathlib import Path

OUT = Path("scripts/gate_worktree_cleanliness_v1.sh")

TEXT = """#!/usr/bin/env bash
set -euo pipefail

# SquadVault — Gate: worktree cleanliness (v1)
#
# Contract (v1):
#   - Snapshot is exact `git status --porcelain=v1 --untracked-files=all` output.
#   - begin: prints snapshot file path (tempfile outside repo).
#   - assert: compares current porcelain to snapshot; prints actionable details on failure.
#   - end: alias of assert with end-of-run label.
#
# CWD-independence:
#   - Always resolves repo root via git.
#
# Idempotence:
#   - No writes under repo; only tempfiles.

die() { echo "ERROR: $*" >&2; exit 1; }

repo_root() {
  git rev-parse --show-toplevel 2>/dev/null || die "not in a git repo"
}

porcelain() {
  local root="$1"
  git -C "$root" status --porcelain=v1 --untracked-files=all
}

cmd="${1:-}"
shift || true

ROOT="$(repo_root)"

case "$cmd" in
  begin)
    snap="$(mktemp -p "${TMPDIR:-/tmp}" sv_worktree_porcelain_XXXXXX)"
    porcelain "$ROOT" > "$snap"
    echo "$snap"
    ;;
  assert)
    snap="${1:-}"; label="${2:-}"
    [[ -n "$snap" ]] || die "assert requires snapshot file path"
    [[ -f "$snap" ]] || die "snapshot file not found: $snap"
    [[ -n "$label" ]] || label="(no label)"

    cur="$(mktemp -p "${TMPDIR:-/tmp}" sv_worktree_porcelain_cur_XXXXXX)"
    porcelain "$ROOT" > "$cur"

    if ! cmp -s "$snap" "$cur"; then
      echo "=== Gate FAIL: worktree cleanliness (v1) ===" >&2
      echo "label: $label" >&2
      echo "repo_root: $ROOT" >&2
      echo "" >&2
      echo "== BEFORE (snapshot porcelain) ==" >&2
      cat "$snap" >&2 || true
      echo "" >&2
      echo "== AFTER (current porcelain) ==" >&2
      cat "$cur" >&2 || true
      echo "" >&2

      # Tracked diff (if any)
      echo "== git diff --name-status (tracked) ==" >&2
      (git -C "$ROOT" diff --name-status || true) >&2
      echo "" >&2

      # Full tracked diff (small repos only; still valuable)
      echo "== git diff (tracked) ==" >&2
      (git -C "$ROOT" diff || true) >&2
      echo "" >&2

      # Untracked listing (derived)
      echo "== untracked files (derived from porcelain) ==" >&2
      # porcelain lines starting with ?? are untracked
      awk '/^\?\? /{sub(/^\?\? /,""); print}' "$cur" >&2 || true
      echo "" >&2

      rm -f "$cur" || true
      exit 1
    fi

    rm -f "$cur" || true
    echo "OK: worktree cleanliness (v1): $label"
    ;;
  end)
    snap="${1:-}"
    [[ -n "$snap" ]] || die "end requires snapshot file path"
    "$0" assert "$snap" "end-of-run"
    ;;
  *)
    die "usage: $0 {begin|assert <snap> <label>|end <snap>}"
    ;;
esac
"""

def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists() and OUT.read_text(encoding="utf-8") == TEXT:
        return
    OUT.write_text(TEXT, encoding="utf-8")

if __name__ == "__main__":
    main()
