#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: allow tracking docs rewrite patcher (v1) ==="

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

PATCHER="scripts/_patch_docs_rewrite_stale_import_refs_v1.py"
UNIGNORE="!${PATCHER}"

if [[ ! -f ".gitignore" ]]; then
  touch .gitignore
fi

# Add unignore line if missing (idempotent)
if ! grep -qF -- "${UNIGNORE}" .gitignore; then
  echo "${UNIGNORE}" >> .gitignore
  echo "OK: added to .gitignore: ${UNIGNORE}"
else
  echo "OK: .gitignore already contains: ${UNIGNORE}"
fi

# Ensure the patcher exists
if [[ ! -f "${PATCHER}" ]]; then
  echo "ERROR: patcher not found: ${PATCHER}" >&2
  exit 2
fi

# Force-add the ignored patcher
git add .gitignore
git add -f "${PATCHER}"

# Amend last commit (keeps history clean)
git commit --amend --no-edit

echo "OK: amended last commit to include .gitignore + ${PATCHER}"
echo "==> git status (porcelain)"
git status --porcelain=v1
echo "OK"
