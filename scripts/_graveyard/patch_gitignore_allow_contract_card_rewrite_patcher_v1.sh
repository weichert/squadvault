#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: allow tracking contract-card rewrite patcher (v1) ==="

# Resolve repo root
if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

PATCHER="scripts/_patch_docs_rewrite_moved_contract_card_refs_v1.py"
UNIGNORE="!${PATCHER}"

# Ensure .gitignore exists
touch .gitignore

# Add unignore line if missing (idempotent)
if ! grep -qF -- "${UNIGNORE}" .gitignore; then
  echo "${UNIGNORE}" >> .gitignore
  echo "OK: added to .gitignore: ${UNIGNORE}"
else
  echo "OK: .gitignore already contains: ${UNIGNORE}"
fi

# Ensure patcher exists
if [[ ! -f "${PATCHER}" ]]; then
  echo "ERROR: patcher not found: ${PATCHER}" >&2
  exit 2
fi

# Stage changes
git add .gitignore
git add -f "${PATCHER}"

# Commit as a new commit (do NOT amend — keeps history clean)
git commit -m "Ops: allowlist contract-card refs rewrite patcher (v1)" || {
  echo "NOTE: no commit created (maybe nothing changed)." >&2
}

echo "OK: patcher now tracked and allowlisted"
echo "==> git status (porcelain)"
git status --porcelain=v1
echo "OK"
