#!/usr/bin/env bash
set -euo pipefail

echo "=== Verify: CI after DB fix (v1) ==="

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

if ! git -C "$repo_root" diff --quiet; then
  echo "ERROR: working tree has unstaged changes; refusing to run prove_ci.sh" >&2
  git -C "$repo_root" status --porcelain=v1 >&2 || true
  exit 1
fi

if test -n "$(git -C "$repo_root" status --porcelain=v1)"; then
  echo "ERROR: working tree not clean; refusing to run prove_ci.sh" >&2
  git -C "$repo_root" status --porcelain=v1 >&2 || true
  exit 1
fi

"$repo_root/scripts/prove_ci.sh"
echo "OK"
