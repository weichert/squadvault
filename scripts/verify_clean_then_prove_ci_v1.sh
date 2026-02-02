#!/usr/bin/env bash
set -euo pipefail

echo "=== Verify: repo clean (no unstaged/untracked) then prove_ci (v1) ==="

self_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$self_dir/.." && pwd)"
cd "$repo_root"

# Untracked?
if [[ -n "$(git ls-files --others --exclude-standard)" ]]; then
  echo "ERROR: untracked files present; refusing to run prove_ci.sh" >&2
  echo "" >&2
  git ls-files --others --exclude-standard >&2
  exit 1
fi

# Unstaged changes?
if ! git diff --quiet; then
  echo "ERROR: unstaged changes present; refusing to run prove_ci.sh" >&2
  echo "" >&2
  git diff --name-only >&2
  exit 1
fi

./scripts/prove_ci.sh
