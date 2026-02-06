#!/usr/bin/env bash
set -euo pipefail
echo "=== Patch: allow tracking CI+Docs hardening freeze patcher (v1) ==="

if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
  cd "${git_root}"
else
  echo "ERROR: not inside git repo" >&2
  exit 2
fi

PATCHER="scripts/_patch_docs_add_ci_docs_hardening_freeze_v1.py"
UNIGNORE="!${PATCHER}"

touch .gitignore
if ! grep -qF -- "${UNIGNORE}" .gitignore; then
  echo "${UNIGNORE}" >> .gitignore
  echo "OK: added to .gitignore: ${UNIGNORE}"
else
  echo "OK: .gitignore already contains: ${UNIGNORE}"
fi

if [[ ! -f "${PATCHER}" ]]; then
  echo "ERROR: patcher not found: ${PATCHER}" >&2
  exit 2
fi

git add .gitignore
git add -f "${PATCHER}"

git commit -m "Ops: allowlist CI+Docs hardening freeze patcher (v1)" || {
  echo "NOTE: no commit created (maybe nothing changed)." >&2
}

echo "OK"
