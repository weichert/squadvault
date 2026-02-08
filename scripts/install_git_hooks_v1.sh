#!/usr/bin/env bash
# SquadVault — install repo git hooks (v1)
#
# Purpose:
#   Install repo-tracked hook templates into .git/hooks (local-only).
#
# Safety:
#   - Never commits .git/hooks
#   - Idempotent
#   - Creates backups of existing hooks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "ERROR: not a git repo."
  exit 2
fi

GIT_DIR="$(git rev-parse --git-dir)"
HOOKS_DIR="${GIT_DIR}/hooks"

src="scripts/git-hooks/pre-commit_v1.sh"
dst="${HOOKS_DIR}/pre-commit"

if [[ ! -f "${src}" ]]; then
  echo "ERROR: missing hook template: ${src}"
  exit 2
fi

mkdir -p "${HOOKS_DIR}"

if [[ -f "${dst}" ]]; then
  # If already identical, no-op.
  if cmp -s "${src}" "${dst}"; then
    echo "OK: pre-commit hook already installed and identical."
    exit 0
  fi

  ts="$(date +%Y%m%d_%H%M%S 2>/dev/null || true)"
  backup="${dst}.bak_${ts:-unknown}"
  cp -p "${dst}" "${backup}"
  echo "NOTE: existing hook backed up to: ${backup}"
fi

cp -p "${src}" "${dst}"
chmod +x "${dst}"
echo "OK: installed ${dst} from ${src}"
echo "TIP: run: ${dst}  (or just commit; git will invoke it)"
