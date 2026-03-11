#!/usr/bin/env bash
set -euo pipefail

echo "=== Ops: Commit Lock E wrapper collapse (v1) ==="

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

# Sanity: apply wrapper must still pass
./scripts/patch_apply_lock_e_final_state.sh

echo
echo "==> git status (pre)"
git status

echo
echo "==> stage + commit"
git add -A

# If nothing to commit, exit cleanly.
if git diff --cached --quiet; then
  echo "OK: nothing staged to commit."
  exit 0
fi

git commit -m "Ops: collapse Lock E apply wrapper to call python patchers directly"

echo
echo "==> tag (lightweight) + push"
tag="lock_e_final_collapsed"
if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
  echo "OK: tag already exists: ${tag}"
else
  git tag -a "${tag}" -m "Lock E final state (collapsed wrapper; python patchers invoked directly)"
  echo "OK: created tag ${tag}"
fi

git push origin main
git push origin "${tag}"

echo
echo "OK: commit + tag + push complete."
