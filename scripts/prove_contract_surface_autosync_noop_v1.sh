#!/usr/bin/env bash
set -euo pipefail

echo "==> Proof: contract surface autosync no-op (v1)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "FAIL: repo must be clean before running autosync no-op proof."
  git status --porcelain=v1
  exit 1
fi

# Run autosync (must not create tracked diffs from canonical repo)
bash scripts/patch_contract_surface_autosync_v2.sh >/dev/null

DIFF_NAMES="$(git diff --name-only | LC_ALL=C sort || true)"
if [[ -n "${DIFF_NAMES}" ]]; then
  echo "FAIL: autosync produced tracked diffs from a clean canonical repo."
  echo "==> Changed files (sorted):"
  printf "%s\n" "${DIFF_NAMES}"
  echo "==> Diff stat:"
  git diff --stat || true

  echo "==> Restoring tracked files to preserve clean repo..."
  git checkout -- .

  if [[ -n "$(git status --porcelain=v1)" ]]; then
    echo "FAIL: repo not clean after restore (unexpected)."
    git status --porcelain=v1
    exit 2
  fi

  exit 1
fi

if [[ -n "$(git status --porcelain=v1)" ]]; then
  echo "FAIL: repo dirty after autosync (unexpected)."
  git status --porcelain=v1
  exit 3
fi

echo "OK: autosync is a no-op on canonical repo."
