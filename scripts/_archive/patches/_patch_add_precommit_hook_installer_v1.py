from __future__ import annotations

from pathlib import Path

HOOK_TEMPLATE = Path("scripts/git-hooks/pre-commit_v1.sh")
INSTALLER = Path("scripts/install_git_hooks_v1.sh")

HOOK_TEXT = """#!/usr/bin/env bash
# SquadVault — git pre-commit hook (v1)
#
# Purpose:
#   Prevent common repo hygiene violations from ever entering commits.
#
# Escape hatch:
#   SV_SKIP_PRECOMMIT=1 -> skip checks, exit 0
#
# Notes:
#   - This file is repo-tracked. It is installed into .git/hooks/pre-commit
#     by scripts/install_git_hooks_v1.sh (installer is idempotent).
#   - Keep bash3-safe.

set -euo pipefail

if [[ "${SV_SKIP_PRECOMMIT:-0}" == "1" ]]; then
  echo "WARN: SV_SKIP_PRECOMMIT=1 set — skipping pre-commit checks."
  exit 0
fi

# Repo-root anchored (pre-commit may be invoked from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

echo "==> pre-commit: terminal banner paste gate"
bash scripts/gate_no_terminal_banner_paste_v1.sh

echo "==> pre-commit: no-xtrace guardrail gate"
bash scripts/gate_no_xtrace_v1.sh

echo "OK: pre-commit checks passed."
"""

INSTALLER_TEXT = """#!/usr/bin/env bash
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
"""

def write_if_changed(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True

def main() -> None:
    changed = False
    changed |= write_if_changed(HOOK_TEMPLATE, HOOK_TEXT)
    changed |= write_if_changed(INSTALLER, INSTALLER_TEXT)

    if not changed:
        print("OK: pre-commit hook template + installer already canonical (v1).")
    else:
        print("OK: wrote/updated pre-commit hook template + installer (v1).")

if __name__ == "__main__":
    main()
